#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import psycopg

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PIPELINE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from public_officer_pipeline import document_guards as guards  # noqa: E402
from public_officer_pipeline.artifact import SourceArtifact, artifact_from_response  # noqa: E402
from public_officer_pipeline.models import PostRef  # noqa: E402
from public_officer_pipeline.storage import R2SourceStorage, SourceStorageError  # noqa: E402


KNOWN_FILE_KINDS = {"html", "pdf", "xlsx", "xls", "hwp", "hwpx", "csv", "txt"}
DEFAULT_REPORT_PATH = Path("/tmp/public-officer-map-r2-backfill-report.json")


@dataclass
class SourceRow:
    id: str
    agency_id: UUID
    url: str | None
    title: str | None
    published_at: date | None
    file_kind: str | None
    hash_sha256: str | None


@dataclass
class RowResult:
    source_id: str
    url: str | None
    status: str
    reason: str | None = None
    storage_path: str | None = None
    hash_sha256: str | None = None
    actual_hash_sha256: str | None = None
    retryable: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill public.sources.storage_path by re-fetching source URLs and archiving them to R2.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Fetch and verify only. This is the default.")
    mode.add_argument("--commit", action="store_true", help="Upload to R2 and update public.sources.storage_path.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum sources to inspect in this run.")
    parser.add_argument("--offset", type=int, default=0, help="Offset into the missing-storage source queue.")
    parser.add_argument("--database-url-env", default="DATABASE_URL", help="Environment variable with write DB URL.")
    parser.add_argument("--r2-env-prefix", default="R2", help="R2 env var prefix, for example R2 or R2_STAGING.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH, help="JSON report output path.")
    parser.add_argument("--retry-file", type=Path, help="Optional newline-delimited retryable failure URL output.")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP fetch timeout in seconds.")
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=guards.MAX_DOCUMENT_DOWNLOAD_BYTES,
        help="Maximum downloaded body bytes per source.",
    )
    return parser.parse_args()


def normalize_file_kind(value: str | None, url: str, content_type: str) -> str | None:
    raw = (value or "").strip().lower().lstrip(".")
    if raw in KNOWN_FILE_KINDS:
        return raw

    lowered_url = url.lower().split("?", 1)[0]
    for suffix in (".pdf", ".xlsx", ".xls", ".hwp", ".hwpx", ".csv", ".txt", ".html", ".htm"):
        if lowered_url.endswith(suffix):
            return "html" if suffix == ".htm" else suffix.lstrip(".")

    lowered_type = content_type.lower()
    if "text/html" in lowered_type:
        return "html"
    if "application/pdf" in lowered_type:
        return "pdf"
    if "spreadsheetml" in lowered_type:
        return "xlsx"
    if "ms-excel" in lowered_type:
        return "xls"
    if "csv" in lowered_type:
        return "csv"
    if lowered_type.startswith("text/"):
        return "txt"
    return None


def load_missing_sources(conn: psycopg.Connection[Any], *, limit: int, offset: int) -> list[SourceRow]:
    rows = conn.execute(
        """
        SELECT id, agency_id, url, title, published_at, file_kind, hash_sha256
        FROM public.sources
        WHERE storage_path IS NULL
        ORDER BY published_at NULLS LAST, id
        LIMIT %s OFFSET %s
        """,
        (limit, offset),
    ).fetchall()
    return [
        SourceRow(
            id=str(row[0]),
            agency_id=row[1],
            url=row[2],
            title=row[3],
            published_at=row[4],
            file_kind=row[5],
            hash_sha256=row[6],
        )
        for row in rows
    ]


def fetch_source(client: httpx.Client, source: SourceRow, *, timeout: float, max_bytes: int) -> SourceArtifact:
    if not source.url:
        raise ValueError("missing source url")

    with client.stream("GET", source.url, timeout=timeout) as response:
        headers = dict(response.headers)
        guards.ensure_content_length_at_most(
            headers,
            max_bytes=max_bytes,
            subject="source document",
        )
        chunks: list[bytes] = []
        total_size = 0
        for chunk in response.iter_bytes():
            total_size += len(chunk)
            guards.ensure_size_at_most(
                size=total_size,
                max_bytes=max_bytes,
                subject="source document body",
            )
            chunks.append(chunk)
        content = b"".join(chunks)
        response.raise_for_status()

    file_kind = normalize_file_kind(source.file_kind, source.url, headers.get("content-type", ""))
    if not file_kind:
        raise LookupError("unknown content type or file kind")

    ref = PostRef(
        agency_id=source.agency_id,
        url=source.url,
        title=source.title or source.url,
        published_at=source.published_at,
        file_kind=file_kind,
    )
    artifact = artifact_from_response(
        ref,
        httpx.Response(
            200,
            headers=headers,
            content=content,
            request=httpx.Request("GET", source.url),
        ),
    )
    artifact.fetched_at = datetime.now(timezone.utc)
    return artifact


def verify_hash(source: SourceRow, artifact: SourceArtifact) -> RowResult | None:
    expected = (source.hash_sha256 or "").strip().lower()
    actual = artifact.hash_sha256.lower()
    if not expected:
        return RowResult(
            source_id=source.id,
            url=source.url,
            status="failed",
            reason="hash_missing",
            actual_hash_sha256=actual,
            retryable=False,
        )
    if expected != actual:
        return RowResult(
            source_id=source.id,
            url=source.url,
            status="failed",
            reason="hash_mismatch",
            hash_sha256=expected,
            actual_hash_sha256=actual,
            retryable=False,
        )
    return None


def planned_storage_path(prefix: str, artifact: SourceArtifact) -> str:
    bucket = os.getenv(f"{prefix}_BUCKET", f"{prefix}_BUCKET")
    key = R2SourceStorage(client=None, bucket=bucket)._artifact_key(artifact)  # type: ignore[arg-type]
    return f"r2://{bucket}/{key}"


def update_storage_path(conn: psycopg.Connection[Any], source_id: str, storage_path: str) -> bool:
    result = conn.execute(
        """
        UPDATE public.sources
        SET storage_path = %s
        WHERE id = %s
          AND storage_path IS NULL
        """,
        (storage_path, source_id),
    )
    conn.commit()
    return result.rowcount == 1


def classify_exception(exc: Exception) -> tuple[str, bool]:
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
        return "fetch_failed", True
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return f"fetch_failed_http_{status}", status in {408, 429, 500, 502, 503, 504}
    if isinstance(exc, guards.DocumentProcessingLimitError):
        return "fetch_failed_size_limit", False
    if isinstance(exc, LookupError):
        return "content_type_unknown", False
    if isinstance(exc, SourceStorageError):
        return "upload_failed", True
    if isinstance(exc, psycopg.Error):
        return "db_update_failed", True
    if isinstance(exc, ValueError):
        return str(exc).replace(" ", "_"), False
    return exc.__class__.__name__, False


def summarize(results: list[RowResult]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
        if result.reason:
            key = f"{result.status}:{result.reason}"
            counts[key] = counts.get(key, 0) + 1
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "results": [asdict(result) for result in results],
    }


def write_reports(report_path: Path, retry_file: Path | None, results: list[RowResult]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summarize(results), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if retry_file:
        retry_file.parent.mkdir(parents=True, exist_ok=True)
        retry_urls = [result.url for result in results if result.retryable and result.url]
        retry_file.write_text("\n".join(retry_urls) + ("\n" if retry_urls else ""), encoding="utf-8")


def main() -> int:
    args = parse_args()
    dry_run = not args.commit
    database_url = os.getenv(args.database_url_env)
    if not database_url:
        raise SystemExit(f"{args.database_url_env} is not configured")

    storage = None if dry_run else R2SourceStorage.from_env(prefix=args.r2_env_prefix)
    results: list[RowResult] = []

    with psycopg.connect(database_url) as conn:
        sources = load_missing_sources(conn, limit=max(args.limit, 0), offset=max(args.offset, 0))
        with httpx.Client(follow_redirects=True, headers={"User-Agent": "PublicOfficerMap-R2Backfill/1.0"}) as client:
            for source in sources:
                try:
                    artifact = fetch_source(client, source, timeout=args.timeout, max_bytes=args.max_bytes)
                    hash_failure = verify_hash(source, artifact)
                    if hash_failure:
                        results.append(hash_failure)
                        continue

                    if dry_run:
                        results.append(
                            RowResult(
                                source_id=source.id,
                                url=source.url,
                                status="planned",
                                hash_sha256=artifact.hash_sha256,
                                storage_path=planned_storage_path(args.r2_env_prefix, artifact),
                            )
                        )
                        continue

                    assert storage is not None
                    storage_path = storage.put_artifact(artifact)
                    if not update_storage_path(conn, source.id, storage_path):
                        results.append(
                            RowResult(
                                source_id=source.id,
                                url=source.url,
                                status="failed",
                                reason="db_update_failed",
                                storage_path=storage_path,
                                hash_sha256=artifact.hash_sha256,
                                retryable=True,
                            )
                        )
                        continue

                    results.append(
                        RowResult(
                            source_id=source.id,
                            url=source.url,
                            status="success",
                            storage_path=storage_path,
                            hash_sha256=artifact.hash_sha256,
                        )
                    )
                except Exception as exc:
                    reason, retryable = classify_exception(exc)
                    results.append(
                        RowResult(
                            source_id=source.id,
                            url=source.url,
                            status="failed",
                            reason=reason,
                            retryable=retryable,
                        )
                    )

    write_reports(args.report, args.retry_file, results)
    summary = summarize(results)
    print(json.dumps({"dry_run": dry_run, "report": str(args.report), **summary["counts"]}, ensure_ascii=False))
    return 1 if any(result.status == "failed" and not result.retryable for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
