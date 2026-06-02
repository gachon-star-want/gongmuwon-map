from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from collections.abc import Awaitable, Callable

from public_officer_pipeline.agencies import (
    CAPITAL_AREA_AGENCIES,
    GYEONGGI_AGENCIES,
    INCHEON_AGENCIES,
    NATIONWIDE_AGENCIES,
    NON_CAPITAL_AGENCIES,
    SEOUL_AGENCIES,
)
from public_officer_pipeline.crawler import (
    AlioItemDisclosureCrawler,
    CleanEyeOwnerWorkCostCrawler,
    CouncilAttachmentCrawler,
    EstimateListCrawler,
    GangnamExpenseCrawler,
    InlineExpenseTableCrawler,
    SeoulOpenGovCrawler,
)
from public_officer_pipeline.source_pattern import (
    AlioItemDisclosurePattern,
    AdapterRequiredPattern,
    AttachmentBoardPattern,
    CleanEyeOwnerWorkCostPattern,
    EstimateListPattern,
    InlineExpenseTablePattern,
    SeoulOpenGovPattern,
    SourcePatternError,
    parse_source_pattern,
)
from public_officer_pipeline.source_registry import (
    source_registry_entries,
    source_registry_summary,
)
from public_officer_pipeline.entity import KakaoResolver
from public_officer_pipeline.extractor import (
    extract_expense_rows,
    extract_hwpx_rows,
    extract_pdf_rows_with_vision,
    extract_spreadsheet_rows,
)
from public_officer_pipeline.loader import PostgresLoader
from public_officer_pipeline.loader.postgres import apply_schema, refresh_materialized_views
from public_officer_pipeline.pipeline.run import (
    PIPELINE_STAGE_PROGRESS,
    ExpenseCrawler,
    PipelineRunConfig,
    PipelineRunner,
)
from public_officer_pipeline.models import (
    Agency,
    ParsedExpenseRow,
    PipelineConfigError,
    PipelineStats,
    PostDetail,
)
from public_officer_pipeline.normalizer import Normalizer
from public_officer_pipeline.storage import SourceStorage, SourceStorageError, R2SourceStorage, NullSourceStorage


AGENCY_SCOPE_CHOICES = [
    "seoul",
    "gyeonggi",
    "incheon",
    "capital-area",
    "gyeongsang",
    "jeolla",
    "chungcheong",
    "gangwon",
    "jeju",
    "non-capital",
    "nationwide",
]

REGIONAL_SCOPE_PARENT_REGIONS = {
    "gyeongsang": {"부산광역시", "대구광역시", "울산광역시", "경상북도", "경상남도"},
    "jeolla": {"광주광역시", "전북특별자치도", "전라남도"},
    "chungcheong": {"대전광역시", "세종특별자치시", "충청북도", "충청남도"},
    "gangwon": {"강원특별자치도"},
    "jeju": {"제주특별자치도"},
}


def _add_write_target_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--confirm-production-write",
        action="store_true",
        help="Required for production writes.",
    )
    parser.add_argument(
        "--write-target",
        choices=["staging", "production"],
        default="staging",
        help="Non-dry-run writes default to DATABASE_URL_STAGING. Production requires explicit opt-in.",
    )
    parser.add_argument(
        "--allow-production-write",
        action="store_true",
        help="Second explicit opt-in for production writes. Must be paired with --confirm-production-write.",
    )
    parser.add_argument(
        "--production-gate-report",
        type=Path,
        help=(
            "Required for non-Seoul production batch writes. The report must contain "
            "a ready nationwide verification verdict."
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="public-officer-pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run-seoul-city", help="Crawl and load Seoul City Hall expense data")
    run.add_argument("--since", type=date.fromisoformat, default=date.today() - timedelta(days=31))
    run.add_argument("--row-since", type=date.fromisoformat)
    run.add_argument("--limit-pages", type=int, default=3)
    run.add_argument("--max-posts", type=int, default=10)
    run.add_argument("--skip-posts", type=int, default=0)
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--allow-deterministic-normalizer", action="store_true")
    run.add_argument("--allow-unmatched-places", action="store_true")
    run.add_argument("--allow-missing-r2", action="store_true")
    run.add_argument(
        "--quality-mode",
        choices=["warn", "quarantine", "fail"],
        default="warn",
        help="Quality gate action: warn, quarantine, fail",
    )
    _add_write_target_args(run)

    opengov = subparsers.add_parser(
        "run-opengov-agency",
        help="Crawl and load a Seoul OpenGov-backed agency from the agency master",
    )
    opengov.add_argument("agency", help="Agency UUID, name, or short_name")
    opengov.add_argument("--since", type=date.fromisoformat, default=date.today() - timedelta(days=31))
    opengov.add_argument("--row-since", type=date.fromisoformat)
    opengov.add_argument("--limit-pages", type=int, default=3)
    opengov.add_argument("--max-posts", type=int, default=10)
    opengov.add_argument("--skip-posts", type=int, default=0)
    opengov.add_argument("--dry-run", action="store_true")
    opengov.add_argument("--allow-deterministic-normalizer", action="store_true")
    opengov.add_argument("--allow-unmatched-places", action="store_true")
    opengov.add_argument("--allow-missing-r2", action="store_true")
    opengov.add_argument(
        "--quality-mode",
        choices=["warn", "quarantine", "fail"],
        default="warn",
        help="Quality gate action: warn, quarantine, fail",
    )
    _add_write_target_args(opengov)

    agency_run = subparsers.add_parser(
        "run-agency",
        help="Crawl and load a supported agency from the agency master",
    )
    agency_run.add_argument("agency", help="Agency UUID, name, or short_name")
    agency_run.add_argument("--since", type=date.fromisoformat, default=date.today() - timedelta(days=31))
    agency_run.add_argument("--row-since", type=date.fromisoformat)
    agency_run.add_argument("--limit-pages", type=int, default=3)
    agency_run.add_argument("--max-posts", type=int, default=10)
    agency_run.add_argument("--skip-posts", type=int, default=0)
    agency_run.add_argument("--dry-run", action="store_true")
    agency_run.add_argument("--allow-deterministic-normalizer", action="store_true")
    agency_run.add_argument("--allow-unmatched-places", action="store_true")
    agency_run.add_argument("--allow-missing-r2", action="store_true")
    agency_run.add_argument(
        "--quality-mode",
        choices=["warn", "quarantine", "fail"],
        default="warn",
        help="Quality gate action: warn, quarantine, fail",
    )
    _add_write_target_args(agency_run)

    agency_batch = subparsers.add_parser(
        "run-agencies",
        help="Run supported agencies with bounded concurrency and summarize skipped adapter_required agencies",
    )
    agency_batch.add_argument(
        "--scope",
        choices=AGENCY_SCOPE_CHOICES,
        default="capital-area",
    )
    agency_batch.add_argument(
        "--agency",
        action="append",
        default=[],
        help="Agency UUID, name, or short_name. Repeat to run an explicit subset.",
    )
    agency_batch.add_argument("--since", type=date.fromisoformat, default=date.today() - timedelta(days=31))
    agency_batch.add_argument("--row-since", type=date.fromisoformat)
    agency_batch.add_argument("--limit-pages", type=int, default=3)
    agency_batch.add_argument("--max-posts", type=int, default=10)
    agency_batch.add_argument("--skip-posts", type=int, default=0)
    agency_batch.add_argument("--dry-run", action="store_true")
    agency_batch.add_argument("--allow-deterministic-normalizer", action="store_true")
    agency_batch.add_argument("--allow-unmatched-places", action="store_true")
    agency_batch.add_argument("--allow-missing-r2", action="store_true")
    agency_batch.add_argument(
        "--quality-mode",
        choices=["warn", "quarantine", "fail"],
        default="warn",
        help="Quality gate action: warn, quarantine, fail",
    )
    agency_batch.add_argument(
        "--concurrency",
        type=int,
        default=6,
        help="Number of agencies to process concurrently. Safety cap: 20.",
    )
    agency_batch.add_argument(
        "--max-attempts",
        type=int,
        default=5,
        help="Maximum attempts for retryable agency failures. Safety cap: 5.",
    )
    agency_batch.add_argument(
        "--retry-delay-seconds",
        type=float,
        default=0.0,
        help="Delay between retry attempts for the same agency.",
    )
    agency_batch.add_argument(
        "--agency-timeout-seconds",
        type=float,
        default=0.0,
        help="Wall-clock timeout for each agency across all attempts. 0 disables the timeout.",
    )
    _add_write_target_args(agency_batch)

    schema = subparsers.add_parser("apply-schema", help="Apply the Postgres schema to the selected write target")
    schema.add_argument(
        "--migration",
        type=Path,
        default=Path("supabase/migrations/20260523235106_initial.sql"),
    )
    _add_write_target_args(schema)

    seed = subparsers.add_parser("seed-agencies", help="Seed agencies into the selected write target")
    seed.add_argument(
        "--scope",
        choices=AGENCY_SCOPE_CHOICES,
        default="seoul",
        help="Default remains seoul for v1 compatibility.",
    )
    _add_write_target_args(seed)
    source_registry = subparsers.add_parser(
        "source-registry",
        help="Print agency source verification status without crawling or DB writes",
    )
    source_registry.add_argument(
        "--scope",
        choices=AGENCY_SCOPE_CHOICES,
        default="capital-area",
    )
    source_registry.add_argument("--format", choices=["json", "jsonl"], default="json")
    source_registry.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the registry summary. Useful for verification reports.",
    )
    refresh_views = subparsers.add_parser("refresh-views", help="Refresh grade and agency stats materialized views")
    _add_write_target_args(refresh_views)

    args = parser.parse_args(argv)
    if args.command == "run-seoul-city":
        write_target_error = _validate_write_target(args)
        if write_target_error is not None:
            return write_target_error
        return asyncio.run(_run_opengov_agency(args, Agency()))
    if args.command == "run-opengov-agency":
        write_target_error = _validate_write_target(args)
        if write_target_error is not None:
            return write_target_error
        agency, lookup_error = _resolve_agency(args.agency)
        if agency is None:
            print(json.dumps(lookup_error, ensure_ascii=False), file=sys.stderr)
            return 2
        try:
            pattern = parse_source_pattern(agency)
        except SourcePatternError as exc:
            print(
                json.dumps(
                    {
                        "error": "unsupported_adapter",
                        "agency": agency.short_name,
                        "adapter": agency.source_pattern.get("adapter"),
                        "reason": str(exc),
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 2
        if not isinstance(pattern, SeoulOpenGovPattern):
            print(
                json.dumps(
                    {
                        "error": "unsupported_adapter",
                        "agency": agency.short_name,
                        "adapter": agency.source_pattern.get("adapter"),
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 2
        return asyncio.run(_run_opengov_agency(args, agency))
    if args.command == "run-agency":
        write_target_error = _validate_write_target(args)
        if write_target_error is not None:
            return write_target_error
        agency, lookup_error = _resolve_agency(args.agency)
        if agency is None:
            print(json.dumps(lookup_error, ensure_ascii=False), file=sys.stderr)
            return 2
        return asyncio.run(_run_supported_agency(args, agency))
    if args.command == "run-agencies":
        return asyncio.run(_run_agencies(args))
    if args.command == "apply-schema":
        write_target_error = _validate_write_target(args)
        if write_target_error is not None:
            return write_target_error
        return _apply_schema(args)
    if args.command == "seed-agencies":
        write_target_error = _validate_write_target(args)
        if write_target_error is not None:
            return write_target_error
        return asyncio.run(_seed_agencies(args))
    if args.command == "source-registry":
        return _print_source_registry(args)
    if args.command == "refresh-views":
        write_target_error = _validate_write_target(args)
        if write_target_error is not None:
            return write_target_error
        return _refresh_views(args)
    return 2


def _agencies_for_scope(scope: str) -> list[Agency]:
    if scope == "seoul":
        return SEOUL_AGENCIES
    if scope == "gyeonggi":
        return GYEONGGI_AGENCIES
    if scope == "incheon":
        return INCHEON_AGENCIES
    if scope == "capital-area":
        return CAPITAL_AREA_AGENCIES
    if scope in REGIONAL_SCOPE_PARENT_REGIONS:
        parent_regions = REGIONAL_SCOPE_PARENT_REGIONS[scope]
        return [agency for agency in NON_CAPITAL_AGENCIES if agency.parent_region in parent_regions]
    if scope == "non-capital":
        return NON_CAPITAL_AGENCIES
    if scope == "nationwide":
        return NATIONWIDE_AGENCIES
    raise ValueError(f"unknown agency scope: {scope}")


def _print_source_registry(args: argparse.Namespace) -> int:
    entries = source_registry_entries(_agencies_for_scope(args.scope))
    summary = source_registry_summary(entries)
    if args.summary_only:
        print(json.dumps({"summary": summary.model_dump()}, ensure_ascii=False, indent=2))
        return 0

    if args.format == "jsonl":
        for entry in entries:
            print(entry.model_dump_json())
        return 0

    print(
        json.dumps(
            {
                "summary": summary.model_dump(),
                "entries": [entry.model_dump() for entry in entries],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _apply_schema(args: argparse.Namespace) -> int:
    try:
        apply_schema(database_url=_database_url_for_write_target(args), migration_path=args.migration)
        print(
            json.dumps(
                {"ok": True, "migration": str(args.migration), "write_target": args.write_target},
                ensure_ascii=False,
            )
        )
        return 0
    except SourceStorageError as exc:
        print(
            json.dumps({"error": "config_error", "message": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 3
    except PipelineConfigError as exc:
        print(json.dumps({"error": "config_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3


async def _seed_agencies(args: argparse.Namespace) -> int:
    try:
        loader = _loader_for_write_target(args)
        agencies = _agencies_for_scope(args.scope)
        seeded_count = await loader.seed_agencies(agencies)
        print(
            json.dumps(
                {
                    "ok": True,
                    "scope": args.scope,
                    "seeded_agencies": seeded_count,
                    "write_target": args.write_target,
                },
                ensure_ascii=False,
            )
        )
        return 0
    except PipelineConfigError as exc:
        print(json.dumps({"error": "config_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3


def _refresh_views(args: argparse.Namespace) -> int:
    try:
        refresh_materialized_views(database_url=_database_url_for_write_target(args))
        print(
            json.dumps(
                {
                    "ok": True,
                    "refreshed": ["place_grade_v1", "agency_stats_v1"],
                    "write_target": args.write_target,
                }
            )
        )
        return 0
    except PipelineConfigError as exc:
        print(json.dumps({"error": "config_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3


def _find_agency(value: str) -> Agency | None:
    agency, _ = _resolve_agency(value)
    return agency


def _resolve_agency(value: str) -> tuple[Agency | None, dict[str, object]]:
    matches = [
        agency
        for agency in NATIONWIDE_AGENCIES
        if value in {str(agency.id), agency.name, agency.short_name}
    ]
    if len(matches) == 1:
        return matches[0], {}
    if len(matches) > 1:
        return None, {
            "error": "ambiguous_agency",
            "agency": value,
            "matches": [
                {
                    "id": str(agency.id),
                    "name": agency.name,
                    "short_name": agency.short_name,
                    "parent_region": agency.parent_region,
                }
                for agency in matches
            ],
        }
    return None, {"error": "unknown_agency", "agency": value}


async def _run_opengov_agency(args: argparse.Namespace, agency: Agency) -> int:
    status, payload = await _run_opengov_agency_result(args, agency)
    return _emit_run_payload(status, payload)


async def _run_opengov_agency_result(
    args: argparse.Namespace,
    agency: Agency,
) -> tuple[int, dict[str, object]]:
    pattern = parse_source_pattern(agency)
    if not isinstance(pattern, SeoulOpenGovPattern):
        raise PipelineConfigError("run-opengov-agency requires seoul_opengov pattern")
    crawler = SeoulOpenGovCrawler(agency=agency, source_pattern=pattern)
    return await _run_crawler_result(args, agency, crawler, _extract_detail_rows)


async def _run_supported_agency(args: argparse.Namespace, agency: Agency) -> int:
    status, payload = await _run_supported_agency_result(args, agency)
    return _emit_run_payload(status, payload)


async def _run_supported_agency_result(
    args: argparse.Namespace,
    agency: Agency,
) -> tuple[int, dict[str, object]]:
    hold_failure_reason = _source_pattern_hold_failure_reason(agency)
    if hold_failure_reason:
        return 2, {
            "error": "adapter_required",
            "agency": agency.short_name,
            "adapter": agency.source_pattern.get("adapter"),
            "failure_reason": hold_failure_reason,
        }

    try:
        pattern = parse_source_pattern(agency)
    except SourcePatternError as exc:
        return 2, {
            "error": "unsupported_adapter",
            "agency": agency.short_name,
            "adapter": agency.source_pattern.get("adapter"),
            "reason": str(exc),
        }

    if isinstance(pattern, AdapterRequiredPattern):
        return 2, {"error": "adapter_required", "agency": agency.short_name, "adapter": pattern.adapter}

    if isinstance(pattern, SeoulOpenGovPattern):
        return await _run_opengov_agency_result(args, agency)
    if isinstance(pattern, AttachmentBoardPattern) and pattern.adapter == "gangnam_xlsx_board":
        return await _run_crawler_result(
            args,
            agency,
            GangnamExpenseCrawler(agency=agency),
            _extract_detail_rows,
        )
    if isinstance(pattern, AttachmentBoardPattern):
        return await _run_crawler_result(
            args,
            agency,
            CouncilAttachmentCrawler(agency=agency, source_pattern=pattern),
            _extract_detail_rows,
        )
    if isinstance(pattern, EstimateListPattern):
        return await _run_crawler_result(
            args,
            agency,
            EstimateListCrawler(agency=agency, source_pattern=pattern),
            _extract_detail_rows,
        )
    if isinstance(pattern, InlineExpenseTablePattern):
        return await _run_crawler_result(
            args,
            agency,
            InlineExpenseTableCrawler(agency=agency, source_pattern=pattern),
            _extract_detail_rows,
        )
    if isinstance(pattern, AlioItemDisclosurePattern):
        return await _run_crawler_result(
            args,
            agency,
            AlioItemDisclosureCrawler(agency=agency, source_pattern=pattern),
            _extract_detail_rows,
        )
    if isinstance(pattern, CleanEyeOwnerWorkCostPattern):
        return await _run_crawler_result(
            args,
            agency,
            CleanEyeOwnerWorkCostCrawler(agency=agency, source_pattern=pattern),
            _extract_detail_rows,
        )
    return 2, {
        "error": "unsupported_adapter",
        "agency": agency.short_name,
        "adapter": pattern.adapter,
    }


async def _run_agencies(args: argparse.Namespace) -> int:
    if args.concurrency < 1 or args.concurrency > 20:
        print(
            json.dumps(
                {
                    "error": "invalid_concurrency",
                    "message": "concurrency must be between 1 and 20",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    args.max_attempts = getattr(args, "max_attempts", 5)
    args.retry_delay_seconds = getattr(args, "retry_delay_seconds", 0.0)
    args.agency_timeout_seconds = getattr(args, "agency_timeout_seconds", 0.0)
    if args.max_attempts < 1 or args.max_attempts > 5:
        print(
            json.dumps(
                {
                    "error": "invalid_max_attempts",
                    "message": "max-attempts must be between 1 and 5",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    if args.retry_delay_seconds < 0:
        print(
            json.dumps(
                {
                    "error": "invalid_retry_delay",
                    "message": "retry-delay-seconds must be non-negative",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    if args.agency_timeout_seconds < 0:
        print(
            json.dumps(
                {
                    "error": "invalid_agency_timeout",
                    "message": "agency-timeout-seconds must be non-negative",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2

    write_target_error = _validate_write_target(args)
    if write_target_error is not None:
        return write_target_error

    if args.agency:
        agencies = []
        for value in args.agency:
            agency, lookup_error = _resolve_agency(value)
            if agency is None:
                print(json.dumps(lookup_error, ensure_ascii=False), file=sys.stderr)
                return 2
            agencies.append(agency)
    else:
        agencies = _agencies_for_scope(args.scope)

    semaphore = asyncio.Semaphore(args.concurrency)
    results: list[dict[str, object]] = []

    async def run_one(agency: Agency) -> None:
        async with semaphore:
            hold_failure_reason = _source_pattern_hold_failure_reason(agency)
            if hold_failure_reason:
                results.append(
                    {
                        "agency_id": str(agency.id),
                        "short_name": agency.short_name,
                        "parent_region": agency.parent_region,
                        "adapter": agency.source_pattern.get("adapter"),
                        "status_code": 2,
                        "result": "adapter_required",
                        "failure_reason": hold_failure_reason,
                        "attempt_count": 0,
                        "max_attempts": args.max_attempts,
                        "attempts": [],
                    }
                )
                return

            try:
                pattern = parse_source_pattern(agency)
                adapter = pattern.adapter
                skipped_adapter_required = isinstance(pattern, AdapterRequiredPattern)
            except SourcePatternError:
                adapter = agency.source_pattern.get("adapter")
                skipped_adapter_required = False

            if skipped_adapter_required:
                failure_reason = _adapter_required_failure_reason(agency)
                results.append(
                    {
                        "agency_id": str(agency.id),
                        "short_name": agency.short_name,
                        "parent_region": agency.parent_region,
                        "adapter": adapter,
                        "status_code": 2,
                        "result": "adapter_required",
                        "failure_reason": failure_reason,
                        "attempt_count": 0,
                        "max_attempts": args.max_attempts,
                        "attempts": [],
                    }
                )
                return

            results.append(await _run_agency_with_retries(args, agency, adapter))

    await asyncio.gather(*(run_one(agency) for agency in agencies))

    success_count = sum(1 for item in results if item["result"] == "success")
    adapter_required_count = sum(1 for item in results if item["result"] == "adapter_required")
    unsupported_count = sum(1 for item in results if item["result"] == "unsupported")
    config_error_count = sum(1 for item in results if item["result"] == "config_error")
    failed_count = sum(1 for item in results if item["result"] == "failed")
    summary = {
        "ok": unsupported_count == 0 and config_error_count == 0 and failed_count == 0,
        "scope": args.scope,
        "dry_run": args.dry_run,
        "write_target": args.write_target,
        "concurrency": args.concurrency,
        "max_attempts": args.max_attempts,
        "agency_timeout_seconds": args.agency_timeout_seconds,
        "total": len(results),
        "success": success_count,
        "adapter_required": adapter_required_count,
        "unsupported": unsupported_count,
        "config_error": config_error_count,
        "failed": failed_count,
        "posts_seen": sum(_int_stat(item, "posts_seen") for item in results),
        "posts_fetched": sum(_int_stat(item, "posts_fetched") for item in results),
        "raw_parsed_rows": sum(_int_stat(item, "raw_parsed_rows") for item in results),
        "parsed_rows": sum(_int_stat(item, "parsed_rows") for item in results),
        "normalized_visits": sum(_int_stat(item, "normalized_visits") for item in results),
        "places_seen": sum(_int_stat(item, "places_seen") for item in results),
        "kakao_matched_places": sum(_int_stat(item, "kakao_matched_places") for item in results),
        "loaded_sources": sum(_int_stat(item, "loaded_sources") for item in results),
        "loaded_places": sum(_int_stat(item, "loaded_places") for item in results),
        "loaded_visits": sum(_int_stat(item, "loaded_visits") for item in results),
        "skipped_invalid_places": sum(_int_stat(item, "skipped_invalid_places") for item in results),
        "failure_reasons": dict(
            Counter(
                str(item["failure_reason"])
                for item in results
                if item.get("failure_reason") is not None
            )
        ),
    }
    print(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 3


async def _run_agency_with_retries(
    args: argparse.Namespace,
    agency: Agency,
    adapter: str | None,
) -> dict[str, object]:
    attempts: list[dict[str, object]] = []
    final_status = 1
    final_payload: dict[str, object] = {"error": "not_run"}
    failure_reason: str | None = "unknown"
    deadline = (
        asyncio.get_running_loop().time() + args.agency_timeout_seconds
        if args.agency_timeout_seconds
        else None
    )

    for attempt in range(1, args.max_attempts + 1):
        progress: dict[str, object] = {
            "current_stage": "start_attempt",
            "last_stage": "start_attempt",
            "stage_elapsed_ms": {},
        }
        progress_token = PIPELINE_STAGE_PROGRESS.set(progress)
        try:
            if deadline is None:
                status, payload = await _run_supported_agency_result(args, agency)
            else:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    raise asyncio.TimeoutError
                status, payload = await asyncio.wait_for(
                    _run_supported_agency_result(args, agency),
                    timeout=remaining,
                )
        except asyncio.TimeoutError:
            stage_elapsed_ms = progress.get("stage_elapsed_ms") or {}
            stats_payload = progress.get("stats")
            status = 1
            payload = {
                "error": "timeout",
                "message": f"agency timed out after {args.agency_timeout_seconds:g} seconds",
                "current_stage": progress.get("current_stage") or "unknown",
                "timeout_stage": _timeout_stage_from_progress(progress, args.agency_timeout_seconds),
                "last_stage": progress.get("last_stage") or "unknown",
                "stage_elapsed_ms": stage_elapsed_ms,
            }
            if isinstance(stats_payload, dict):
                payload.update({key: stats_payload.get(key, 0) for key in _STAT_KEYS})
        except Exception as exc:
            status = 1
            payload = {"error": "exception", "message": str(exc)}
        finally:
            PIPELINE_STAGE_PROGRESS.reset(progress_token)

        final_status = status
        final_payload = payload
        failure_reason = _classify_failure_reason(status, payload, agency=agency)
        attempts.append(
            {
                "attempt": attempt,
                "status_code": status,
                "result": _batch_result_label(status, skipped_adapter_required=False),
                "failure_reason": failure_reason,
                "error": _safe_error_message(payload) if status != 0 else None,
            }
        )
        if status == 0 or not _should_retry_batch_failure(status, failure_reason):
            break
        if args.retry_delay_seconds:
            sleep_for = args.retry_delay_seconds
            if deadline is not None:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    break
                sleep_for = min(sleep_for, remaining)
            await asyncio.sleep(sleep_for)

    result = _batch_result_label(final_status, skipped_adapter_required=False)
    item: dict[str, object] = {
        "agency_id": str(agency.id),
        "short_name": agency.short_name,
        "parent_region": agency.parent_region,
        "adapter": adapter,
        "status_code": final_status,
        "result": result,
        "failure_reason": None if final_status == 0 else failure_reason,
        "attempt_count": len(attempts),
        "max_attempts": args.max_attempts,
        "attempts": attempts,
    }
    item.update({key: final_payload.get(key, 0) for key in _STAT_KEYS})
    if final_status == 0:
        item["kakao_match_rate"] = final_payload.get("kakao_match_rate", 0)
    else:
        item["error"] = _safe_error_message(final_payload)
        if "kakao_match_rate" in final_payload:
            item["kakao_match_rate"] = final_payload["kakao_match_rate"]
    for key in _DIAGNOSTIC_KEYS:
        if key in final_payload:
            item[key] = final_payload[key]
    return item


def _validate_write_target(args: argparse.Namespace) -> int | None:
    if getattr(args, "dry_run", False):
        return None
    if args.write_target == "staging":
        if not _staging_database_url():
            print(
                json.dumps(
                    {
                        "error": "staging_database_url_required",
                        "message": (
                            "Staging writes require DATABASE_URL_STAGING or "
                            "STAGING_DATABASE_URL. Use --dry-run first."
                        ),
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 2
        if _requires_raw_artifact_storage(args) and not getattr(args, "allow_missing_r2", False):
            missing_r2 = _missing_r2_env_vars(args)
            if missing_r2:
                print(
                    json.dumps(
                        {
                            "error": "staging_r2_required",
                            "message": (
                                "Staging writes require R2 env vars for raw artifact provenance."
                            ),
                            "missing": missing_r2,
                        },
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                )
                return 2
        return None
    if args.write_target == "production":
        if not args.confirm_production_write:
            print(
                json.dumps(
                    {
                        "error": "confirmation_required",
                        "message": "Production writes require --confirm-production-write.",
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 2
        if not args.allow_production_write:
            print(
                json.dumps(
                    {
                        "error": "production_write_opt_in_required",
                        "message": (
                            "Production writes require --allow-production-write and "
                            "--confirm-production-write."
                        ),
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 2
        gate_error = _production_gate_error(args)
        if gate_error is not None:
            print(json.dumps(gate_error, ensure_ascii=False), file=sys.stderr)
            return 2

    return None


def _staging_database_url() -> str | None:
    return os.getenv("DATABASE_URL_STAGING") or os.getenv("STAGING_DATABASE_URL")


def _missing_r2_env_vars(args: argparse.Namespace) -> list[str]:
    names = _r2_env_var_names(_r2_env_prefix(args))
    return [name for name in names if not os.getenv(name)]


def _r2_env_prefix(args: argparse.Namespace) -> str:
    generic_prefix = "R2"
    staging_prefix = "R2_STAGING"
    if getattr(args, "write_target", None) == "staging" and _has_all_env_vars(
        _r2_env_var_names(staging_prefix)
    ):
        return staging_prefix
    return generic_prefix


def _r2_env_var_names(prefix: str) -> tuple[str, str, str, str]:
    return (
        f"{prefix}_ACCOUNT_ID",
        f"{prefix}_ACCESS_KEY_ID",
        f"{prefix}_SECRET_ACCESS_KEY",
        f"{prefix}_BUCKET",
    )


def _has_all_env_vars(names: tuple[str, ...]) -> bool:
    return all(os.getenv(name) for name in names)


def _requires_raw_artifact_storage(args: argparse.Namespace) -> bool:
    command = getattr(args, "command", None)
    if command is None:
        return True
    return command in {"run-seoul-city", "run-opengov-agency", "run-agency", "run-agencies"}


def _database_url_for_write_target(args: argparse.Namespace) -> str | None:
    if getattr(args, "write_target", None) == "staging":
        staging_url = _staging_database_url()
        if not staging_url:
            raise PipelineConfigError(
                "DATABASE_URL_STAGING or STAGING_DATABASE_URL is required for staging writes"
            )
        return staging_url
    return None


def _production_gate_error(args: argparse.Namespace) -> dict[str, str] | None:
    report_path = getattr(args, "production_gate_report", None)
    if not report_path:
        return {
            "error": "production_gate_report_required",
            "message": (
                "Production writes require --production-gate-report "
                "from a passing staging verification run."
            ),
        }

    try:
        report = Path(report_path).read_text(encoding="utf-8")
    except OSError as error:
        return {
            "error": "production_gate_report_unreadable",
            "message": str(error),
        }

    if "서비스 주입 판정: production 주입 검토 가능" not in report:
        return {
            "error": "production_gate_report_not_ready",
            "message": "Verification report does not permit production injection.",
        }
    return None


def _batch_result_label(status: int, skipped_adapter_required: bool) -> str:
    if status == 0:
        return "success"
    if skipped_adapter_required:
        return "adapter_required"
    if status == 2:
        return "unsupported"
    if status == 3:
        return "config_error"
    return "failed"


_STAT_KEYS = (
    "posts_seen",
    "posts_fetched",
    "raw_parsed_rows",
    "parsed_rows",
    "normalized_visits",
    "places_seen",
    "kakao_matched_places",
    "loaded_sources",
    "loaded_places",
    "loaded_visits",
    "skipped_invalid_places",
)

_DIAGNOSTIC_KEYS = (
    "current_stage",
    "last_stage",
    "timeout_stage",
    "stage_elapsed_ms",
)


def _timeout_stage_from_progress(progress: dict[str, object], timeout_seconds: float) -> str:
    current_stage = str(progress.get("current_stage") or "unknown")
    elapsed = progress.get("stage_elapsed_ms")
    if not isinstance(elapsed, dict) or not elapsed:
        return current_stage

    timeout_ms = max(0, int(timeout_seconds * 1000))
    overrun_stages = [
        (str(stage), value)
        for stage, value in elapsed.items()
        if isinstance(value, int) and value >= timeout_ms
    ]
    if not overrun_stages:
        return current_stage
    return max(overrun_stages, key=lambda item: item[1])[0]


def _int_stat(item: dict[str, object], key: str) -> int:
    value = item.get(key, 0)
    return value if isinstance(value, int) else 0


def _emit_run_payload(status: int, payload: dict[str, object]) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stdout if status == 0 else sys.stderr)
    return status


def _adapter_required_failure_reason(agency: Agency) -> str:
    raw = agency.source_pattern
    if isinstance(raw, dict):
        hold_status = str(raw.get("holdStatus") or "")
        if hold_status == "legal_hold":
            return "legal_hold"
        if hold_status in {"source_not_found", "no_recent_data", "pdf_vision_hold"}:
            return hold_status
        if hold_status == "adapter_hold":
            return "parser_missing"
    return "source_not_found"


def _source_pattern_hold_failure_reason(agency: Agency) -> str | None:
    raw = agency.source_pattern
    if isinstance(raw, dict) and raw.get("holdStatus"):
        return _adapter_required_failure_reason(agency)
    return None


_RETRYABLE_FAILURE_REASONS = {
    "auth_js_download",
    "llm_extraction_failure",
    "storage_failure",
    "unknown",
}


def _should_retry_batch_failure(status: int, failure_reason: str | None) -> bool:
    return status in {1, 3} and failure_reason in _RETRYABLE_FAILURE_REASONS


def _classify_failure_reason(
    status: int,
    payload: dict[str, object],
    *,
    agency: Agency,
) -> str | None:
    if status == 0:
        return None

    error_code = str(payload.get("error") or payload.get("code") or "")
    if error_code == "adapter_required":
        return _adapter_required_failure_reason(agency)
    if error_code == "unsupported_adapter":
        return "parser_missing"
    if error_code == "timeout":
        return "timeout"

    text = f"{error_code} {_safe_error_message(payload)}".lower()
    if "legal" in text or "visibility" in text:
        return "legal_hold"
    if "parser" in text or "unsupported" in text or "extractor" in text or "decompress" in text:
        return "parser_missing"
    if "kakao" in text or "coordinate" in text or "unmatched" in text:
        return "kakao_resolution"
    if "database" in text or "postgres" in text or "constraint" in text or "duplicate" in text:
        return "db_constraint"
    if "r2" in text or "storage" in text or "bucket" in text or "storage_path" in text:
        return "storage_failure"
    if (
        "llm" in text
        or "api key" in text
        or "vision" in text
        or "confidence" in text
        or "anthropic" in text
        or "openai" in text
        or "gemini" in text
    ):
        return "llm_extraction_failure"
    if (
        "download" in text
        or "timeout" in text
        or "403" in text
        or "401" in text
        or "auth" in text
        or "js" in text
        or "http" in text
        or "dns" in text
        or "netfunnel" in text
    ):
        return "auth_js_download"
    if "source" in text or "not found" in text or "no posts" in text:
        return "source_not_found"
    return "unknown"


def _safe_error_message(payload: dict[str, object]) -> str:
    message = str(payload.get("message") or payload.get("reason") or payload.get("error") or "")
    for env_name in ("DATABASE_URL", "DATABASE_URL_READONLY", "DATABASE_URL_STAGING", "STAGING_DATABASE_URL"):
        secret = os.getenv(env_name)
        if secret:
            message = message.replace(secret, "[redacted]")
    return message


async def _run_crawler(
    args: argparse.Namespace,
    agency: Agency,
    crawler: ExpenseCrawler,
    row_extractor: Callable[[PostDetail], list[ParsedExpenseRow] | Awaitable[list[ParsedExpenseRow]]],
) -> int:
    status, payload = await _run_crawler_result(args, agency, crawler, row_extractor)
    return _emit_run_payload(status, payload)


async def _run_crawler_result(
    args: argparse.Namespace,
    agency: Agency,
    crawler: ExpenseCrawler,
    row_extractor: Callable[[PostDetail], list[ParsedExpenseRow] | Awaitable[list[ParsedExpenseRow]]],
) -> tuple[int, dict[str, object]]:
    try:
        normalizer = Normalizer(allow_deterministic_fallback=args.allow_deterministic_normalizer)
        resolver = KakaoResolver(allow_unmatched_fallback=args.allow_unmatched_places)
        if args.dry_run:
            storage: SourceStorage = NullSourceStorage()
        elif args.allow_missing_r2:
            storage = NullSourceStorage()
        else:
            storage = R2SourceStorage.from_env(prefix=_r2_env_prefix(args))

        loader = None if args.dry_run else _loader_for_write_target(args)
        config = PipelineRunConfig(
            since=args.since,
            row_since=args.row_since,
            limit_pages=args.limit_pages,
            max_posts=args.max_posts,
            skip_posts=args.skip_posts,
            dry_run=args.dry_run,
            quality_mode=args.quality_mode,
        )
        runner = PipelineRunner(
            config=config,
            normalizer=normalizer,
            resolver=resolver,
            storage=storage,
            row_extractor=row_extractor,
            loader=loader,
            require_storage_path=not args.allow_missing_r2,
            extractor_model="llm",
        )
        stats = await runner.run_agency(agency, crawler)

        return 0, stats.model_dump() | {"kakao_match_rate": stats.kakao_match_rate}
    except PipelineConfigError as exc:
        return 3, _pipeline_error_payload(exc)
    except SourceStorageError as exc:
        return 3, {"error": "config_error", "message": str(exc)}


def _pipeline_error_payload(exc: PipelineConfigError) -> dict[str, object]:
    payload: dict[str, object] = {"error": "config_error", "message": str(exc)}
    stats = getattr(exc, "stats", None)
    if isinstance(stats, PipelineStats):
        payload.update(stats.model_dump())
        payload["kakao_match_rate"] = stats.kakao_match_rate
    return payload


def _loader_for_write_target(args: argparse.Namespace) -> PostgresLoader:
    if getattr(args, "write_target", None) == "staging":
        return PostgresLoader(database_url=_database_url_for_write_target(args))
    return PostgresLoader()


async def _extract_detail_rows(detail: PostDetail) -> list[ParsedExpenseRow]:
    if detail.file_kind == "html":
        return extract_expense_rows(detail.html, fallback_date=detail.published_at)
    if detail.file_kind in {"xls", "xlsx"} and detail.content_bytes:
        return extract_spreadsheet_rows(
            detail.content_bytes,
            fallback_department=detail.department_name or "서울특별시",
        )
    if detail.file_kind == "hwpx" and detail.content_bytes:
        return extract_hwpx_rows(
            detail.content_bytes,
            fallback_department=detail.department_name or "서울특별시",
        )
    if detail.file_kind == "pdf" and detail.content_bytes:
        return extract_pdf_rows_with_vision(
            detail.content_bytes,
            fallback_department=detail.department_name or "서울특별시",
            source_title=detail.title,
        )
    return []


if __name__ == "__main__":
    raise SystemExit(main())
