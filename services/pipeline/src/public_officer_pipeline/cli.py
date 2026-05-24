from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from public_officer_pipeline.crawler import SeoulOpenGovCrawler
from public_officer_pipeline.entity import KakaoResolver
from public_officer_pipeline.extractor import extract_expense_rows
from public_officer_pipeline.loader import PostgresLoader
from public_officer_pipeline.loader.postgres import apply_schema
from public_officer_pipeline.models import Agency, NormalizedVisit, PipelineConfigError, PipelineStats
from public_officer_pipeline.normalizer import Normalizer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="public-officer-pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run-seoul-city", help="Crawl and load Seoul City Hall expense data")
    run.add_argument("--since", type=date.fromisoformat, default=date.today() - timedelta(days=31))
    run.add_argument("--limit-pages", type=int, default=3)
    run.add_argument("--max-posts", type=int, default=10)
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--allow-deterministic-normalizer", action="store_true")
    run.add_argument("--allow-unmatched-places", action="store_true")

    schema = subparsers.add_parser("apply-schema", help="Apply the Postgres schema to DATABASE_URL")
    schema.add_argument(
        "--migration",
        type=Path,
        default=Path("supabase/migrations/20260523235106_initial.sql"),
    )

    args = parser.parse_args(argv)
    if args.command == "run-seoul-city":
        return asyncio.run(_run_seoul_city(args))
    if args.command == "apply-schema":
        return _apply_schema(args)
    return 2


def _apply_schema(args: argparse.Namespace) -> int:
    try:
        apply_schema(migration_path=args.migration)
        print(json.dumps({"ok": True, "migration": str(args.migration)}, ensure_ascii=False))
        return 0
    except PipelineConfigError as exc:
        print(json.dumps({"error": "config_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3


async def _run_seoul_city(args: argparse.Namespace) -> int:
    stats = PipelineStats()
    agency = Agency()
    crawler = SeoulOpenGovCrawler()
    normalizer = Normalizer(allow_deterministic_fallback=args.allow_deterministic_normalizer)
    resolver = KakaoResolver(allow_unmatched_fallback=args.allow_unmatched_places)

    try:
        posts = await crawler.list_posts(since=args.since, limit_pages=args.limit_pages)
        stats.posts_seen = len(posts)
        all_visits: list[NormalizedVisit] = []
        resolved_by_place_json = {}
        loaded_sources = loaded_places = loaded_visits = 0
        loader = None if args.dry_run else PostgresLoader()

        for post in posts[: args.max_posts]:
            detail = await crawler.fetch_post(post)
            stats.posts_fetched += 1
            rows = [row for row in extract_expense_rows(detail.html) if row.used_at.date() >= args.since]
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


if __name__ == "__main__":
    raise SystemExit(main())
