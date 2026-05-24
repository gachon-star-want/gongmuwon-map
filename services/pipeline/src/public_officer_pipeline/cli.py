from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from collections.abc import Callable
from typing import Protocol

from public_officer_pipeline.agencies import SEOUL_AGENCIES
from public_officer_pipeline.crawler import (
    CouncilAttachmentCrawler,
    EstimateListCrawler,
    GangnamExpenseCrawler,
    SeoulOpenGovCrawler,
)
from public_officer_pipeline.entity import KakaoResolver
from public_officer_pipeline.extractor import extract_expense_rows, extract_pdf_rows_with_vision, extract_spreadsheet_rows
from public_officer_pipeline.loader import PostgresLoader
from public_officer_pipeline.loader.postgres import apply_schema, refresh_materialized_views
from public_officer_pipeline.models import (
    Agency,
    NormalizedVisit,
    ParsedExpenseRow,
    PipelineConfigError,
    PipelineStats,
    PostDetail,
    PostRef,
)
from public_officer_pipeline.normalizer import Normalizer


class ExpenseCrawler(Protocol):
    async def list_posts(self, since: date, limit_pages: int = 3) -> list[PostRef]: ...

    async def fetch_post(self, ref: PostRef) -> PostDetail: ...

    async def aclose(self) -> None: ...


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="public-officer-pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run-seoul-city", help="Crawl and load Seoul City Hall expense data")
    run.add_argument("--since", type=date.fromisoformat, default=date.today() - timedelta(days=31))
    run.add_argument("--limit-pages", type=int, default=3)
    run.add_argument("--max-posts", type=int, default=10)
    run.add_argument("--skip-posts", type=int, default=0)
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--allow-deterministic-normalizer", action="store_true")
    run.add_argument("--allow-unmatched-places", action="store_true")

    opengov = subparsers.add_parser(
        "run-opengov-agency",
        help="Crawl and load a Seoul OpenGov-backed agency from the agency master",
    )
    opengov.add_argument("agency", help="Agency UUID, name, or short_name")
    opengov.add_argument("--since", type=date.fromisoformat, default=date.today() - timedelta(days=31))
    opengov.add_argument("--limit-pages", type=int, default=3)
    opengov.add_argument("--max-posts", type=int, default=10)
    opengov.add_argument("--skip-posts", type=int, default=0)
    opengov.add_argument("--dry-run", action="store_true")
    opengov.add_argument("--allow-deterministic-normalizer", action="store_true")
    opengov.add_argument("--allow-unmatched-places", action="store_true")

    agency_run = subparsers.add_parser(
        "run-agency",
        help="Crawl and load a supported agency from the agency master",
    )
    agency_run.add_argument("agency", help="Agency UUID, name, or short_name")
    agency_run.add_argument("--since", type=date.fromisoformat, default=date.today() - timedelta(days=31))
    agency_run.add_argument("--limit-pages", type=int, default=3)
    agency_run.add_argument("--max-posts", type=int, default=10)
    agency_run.add_argument("--skip-posts", type=int, default=0)
    agency_run.add_argument("--dry-run", action="store_true")
    agency_run.add_argument("--allow-deterministic-normalizer", action="store_true")
    agency_run.add_argument("--allow-unmatched-places", action="store_true")

    schema = subparsers.add_parser("apply-schema", help="Apply the Postgres schema to DATABASE_URL")
    schema.add_argument(
        "--migration",
        type=Path,
        default=Path("supabase/migrations/20260523235106_initial.sql"),
    )

    subparsers.add_parser("seed-agencies", help="Seed the 52 Seoul v1 agencies into DATABASE_URL")
    subparsers.add_parser("refresh-views", help="Refresh grade and agency stats materialized views")

    args = parser.parse_args(argv)
    if args.command == "run-seoul-city":
        return asyncio.run(_run_opengov_agency(args, Agency()))
    if args.command == "run-opengov-agency":
        agency = _find_agency(args.agency)
        if agency is None:
            print(
                json.dumps({"error": "unknown_agency", "agency": args.agency}, ensure_ascii=False),
                file=sys.stderr,
            )
            return 2
        if agency.source_pattern.get("adapter") != "seoul_opengov":
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
        agency = _find_agency(args.agency)
        if agency is None:
            print(
                json.dumps({"error": "unknown_agency", "agency": args.agency}, ensure_ascii=False),
                file=sys.stderr,
            )
            return 2
        return asyncio.run(_run_supported_agency(args, agency))
    if args.command == "apply-schema":
        return _apply_schema(args)
    if args.command == "seed-agencies":
        return asyncio.run(_seed_agencies())
    if args.command == "refresh-views":
        return _refresh_views()
    return 2


def _apply_schema(args: argparse.Namespace) -> int:
    try:
        apply_schema(migration_path=args.migration)
        print(json.dumps({"ok": True, "migration": str(args.migration)}, ensure_ascii=False))
        return 0
    except PipelineConfigError as exc:
        print(json.dumps({"error": "config_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3


async def _seed_agencies() -> int:
    try:
        loader = PostgresLoader()
        seeded_count = await loader.seed_agencies(SEOUL_AGENCIES)
        print(json.dumps({"ok": True, "seeded_agencies": seeded_count}, ensure_ascii=False))
        return 0
    except PipelineConfigError as exc:
        print(json.dumps({"error": "config_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3


def _refresh_views() -> int:
    try:
        refresh_materialized_views()
        print(json.dumps({"ok": True, "refreshed": ["place_grade_v1", "agency_stats_v1"]}))
        return 0
    except PipelineConfigError as exc:
        print(json.dumps({"error": "config_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3


def _find_agency(value: str) -> Agency | None:
    for agency in SEOUL_AGENCIES:
        if value in {str(agency.id), agency.name, agency.short_name}:
            return agency
    return None


async def _run_opengov_agency(args: argparse.Namespace, agency: Agency) -> int:
    crawler = SeoulOpenGovCrawler(agency=agency)
    return await _run_crawler(args, agency, crawler, _extract_detail_rows)


async def _run_supported_agency(args: argparse.Namespace, agency: Agency) -> int:
    adapter = agency.source_pattern.get("adapter")
    if adapter == "seoul_opengov":
        return await _run_opengov_agency(args, agency)
    if adapter == "gangnam_xlsx_board":
        return await _run_crawler(args, agency, GangnamExpenseCrawler(agency=agency), _extract_detail_rows)
    if adapter == "estimate_list_html":
        return await _run_crawler(args, agency, EstimateListCrawler(agency=agency), _extract_detail_rows)
    if adapter in {"gncouncil_pdf_board", "council_attachment_board", "attachment_board"}:
        return await _run_crawler(args, agency, CouncilAttachmentCrawler(agency=agency), _extract_detail_rows)
    print(
        json.dumps(
            {
                "error": "unsupported_adapter",
                "agency": agency.short_name,
                "adapter": adapter,
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    return 2


async def _run_crawler(
    args: argparse.Namespace,
    agency: Agency,
    crawler: ExpenseCrawler,
    row_extractor: Callable[[PostDetail], list[ParsedExpenseRow]],
) -> int:
    stats = PipelineStats()
    normalizer = Normalizer(allow_deterministic_fallback=args.allow_deterministic_normalizer)
    resolver = KakaoResolver(allow_unmatched_fallback=args.allow_unmatched_places)

    try:
        posts = await crawler.list_posts(since=args.since, limit_pages=args.limit_pages)
        stats.posts_seen = len(posts)
        all_visits: list[NormalizedVisit] = []
        resolved_by_place_json = {}
        loaded_sources = loaded_places = loaded_visits = 0
        loader = None if args.dry_run else PostgresLoader()

        for post in posts[args.skip_posts : args.skip_posts + args.max_posts]:
            detail = await crawler.fetch_post(post)
            stats.posts_fetched += 1
            rows = [row for row in row_extractor(detail) if row.used_at.date() >= args.since]
            stats.parsed_rows += len(rows)
            visits = await normalizer.normalize_rows(
                agency_id=agency.id,
                source_url=detail.url,
                source_title=detail.title,
                source_published_at=detail.published_at,
                source_hash_sha256=detail.hash_sha256,
                rows=rows,
            )
            stats.normalized_visits += len(visits)
            all_visits.extend(visits)

            post_places = {}
            for visit in visits:
                key = visit.place_raw.model_dump_json()
                if key in resolved_by_place_json:
                    post_places[key] = resolved_by_place_json[key]
                    continue
                resolved = await resolver.resolve(visit.place_raw)
                resolved_by_place_json[key] = resolved
                post_places[key] = resolved

            if loader and visits:
                source_count, place_count, visit_count = await loader.load(
                    agency=agency,
                    source_url=detail.url,
                    source_title=detail.title,
                    source_published_at=detail.published_at,
                    source_hash_sha256=detail.hash_sha256,
                    source_file_kind=detail.file_kind,
                    resolved_places=post_places,
                    visits=visits,
                )
                loaded_sources += source_count
                loaded_places += place_count
                loaded_visits += visit_count

        stats.places_seen = len(resolved_by_place_json)
        stats.kakao_matched_places = sum(1 for place in resolved_by_place_json.values() if place.matched)
        stats.loaded_sources = loaded_sources
        stats.loaded_places = loaded_places
        stats.loaded_visits = loaded_visits
        print(json.dumps(stats.model_dump() | {"kakao_match_rate": stats.kakao_match_rate}, ensure_ascii=False, indent=2))
        return 0
    except PipelineConfigError as exc:
        print(json.dumps({"error": "config_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3
    finally:
        await crawler.aclose()


def _extract_detail_rows(detail: PostDetail) -> list[ParsedExpenseRow]:
    if detail.file_kind == "html":
        return extract_expense_rows(detail.html)
    if detail.file_kind in {"xls", "xlsx"} and detail.content_bytes:
        return extract_spreadsheet_rows(
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
