from __future__ import annotations

import inspect
import time
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from datetime import date
from typing import Any, Literal, Protocol

from public_officer_pipeline.entity import KakaoResolver
from public_officer_pipeline.entity.policy import is_valid_place_name
from public_officer_pipeline.legal.visibility import LegalVisibilityError, validate_normalized_visits
from public_officer_pipeline.models import (
    Agency,
    ParsedExpenseRow,
    PipelineConfigError,
    PipelineStats,
    PostDetail,
    PostRef,
    ResolvedPlace,
)
from public_officer_pipeline.normalizer import Normalizer
from public_officer_pipeline.pipeline.batch import LoadBatch, place_resolution_key
from public_officer_pipeline.pipeline.quality import QualityGateResult, evaluate_batch
from public_officer_pipeline.storage import SourceStorage, SourceStorageError

from pydantic import BaseModel

PIPELINE_STAGE_PROGRESS: ContextVar[dict[str, Any] | None] = ContextVar(
    "PIPELINE_STAGE_PROGRESS",
    default=None,
)


class ExpenseCrawler(Protocol):
    async def list_posts(self, since: date, limit_pages: int = 3) -> list[PostRef]: ...

    async def fetch_post(self, ref: PostRef) -> PostDetail: ...

    async def aclose(self) -> None: ...


RowExtractor = Callable[
    [PostDetail],
    list[ParsedExpenseRow] | Awaitable[list[ParsedExpenseRow]],
]


class BatchLoader(Protocol):
    async def load(self, batch: LoadBatch) -> tuple[int, int, int]: ...


class PipelineRunConfig(BaseModel):
    since: date
    row_since: date | None = None
    limit_pages: int
    max_posts: int
    skip_posts: int = 0
    dry_run: bool = False
    quality_mode: Literal["warn", "quarantine", "fail"] = "fail"


class PipelineQualityError(PipelineConfigError):
    def __init__(self, message: str, *, stats: PipelineStats) -> None:
        super().__init__(message)
        self.stats = stats


class PipelineRunner:
    def __init__(
        self,
        *,
        config: PipelineRunConfig,
        normalizer: Normalizer,
        resolver: KakaoResolver,
        storage: SourceStorage,
        row_extractor: RowExtractor,
        loader: BatchLoader | None = None,
        require_storage_path: bool = False,
        extractor_model: str = "llm",
    ) -> None:
        self.config = config
        self.normalizer = normalizer
        self.resolver = resolver
        self.storage = storage
        self.row_extractor = row_extractor
        self.loader = loader
        self.require_storage_path = require_storage_path
        self.extractor_model = extractor_model

    async def run_agency(
        self,
        agency: Agency,
        crawler: ExpenseCrawler,
    ) -> PipelineStats:
        try:
            return await self._run_agency(agency, crawler)
        except SourceStorageError as exc:
            raise PipelineConfigError(str(exc)) from exc

    async def _run_agency(
        self,
        agency: Agency,
        crawler: ExpenseCrawler,
    ) -> PipelineStats:
        stats = PipelineStats()
        quality_results: list[QualityGateResult] = []
        resolved_by_place_key: dict[str, ResolvedPlace] = {}

        try:
            try:
                _mark_stage(stats, "list_posts")
                posts = await crawler.list_posts(
                    since=self.config.since,
                    limit_pages=self.config.limit_pages,
                )
                stats.posts_seen = len(posts)

                for post in posts[self.config.skip_posts : self.config.skip_posts + self.config.max_posts]:
                    _mark_stage(stats, "fetch_post")
                    detail = await crawler.fetch_post(post)
                    stats.posts_fetched += 1

                    _mark_stage(stats, "store_artifact")
                    storage_path = self.storage.put_artifact(detail)

                    _mark_stage(stats, "extract_rows")
                    extracted_rows = self.row_extractor(detail)
                    raw_rows = (
                        await extracted_rows
                        if inspect.isawaitable(extracted_rows)
                        else extracted_rows
                    )
                    stats.raw_parsed_rows += len(raw_rows)
                    row_since = self.config.row_since or self.config.since
                    rows = [row for row in raw_rows if row.used_at.date() >= row_since]
                    stats.parsed_rows += len(rows)

                    _mark_stage(stats, "normalize_rows")
                    raw_visits = await self.normalizer.normalize_rows(
                        agency_id=agency.id,
                        agency=agency,
                        source_url=detail.url,
                        source_title=detail.title,
                        source_published_at=detail.published_at,
                        source_hash_sha256=detail.hash_sha256,
                        rows=rows,
                    )

                    try:
                        _mark_stage(stats, "validate_visits")
                        visits = validate_normalized_visits(raw_visits, agency=agency)
                    except LegalVisibilityError as exc:
                        quality = [
                            QualityGateResult(
                                ok=False,
                                severity="fail",
                                code="legal_visibility",
                                message=f"legal visibility validation failed: {exc}",
                            )
                        ]
                        quality_results.extend(quality)
                        if self.config.quality_mode != "warn":
                            raise PipelineConfigError(str(quality[0].message))
                        continue

                    stats.normalized_visits += len(visits)
                    valid_place_visits = [
                        visit for visit in visits if is_valid_place_name(visit.place_raw.name)
                    ]
                    stats.skipped_invalid_places += len(visits) - len(valid_place_visits)
                    visits = valid_place_visits
                    if not visits:
                        continue

                    post_resolved: dict[str, ResolvedPlace] = {}
                    for visit in visits:
                        key = place_resolution_key(visit.place_raw)
                        if key in resolved_by_place_key:
                            post_resolved[key] = resolved_by_place_key[key]
                            continue
                        _mark_stage(stats, "resolve_places")
                        resolved = await self.resolver.resolve(visit.place_raw)
                        resolved_by_place_key[key] = resolved
                        post_resolved[key] = resolved

                    _mark_stage(stats, "evaluate_quality")
                    batch = LoadBatch(
                        agency=agency,
                        source_url=detail.url,
                        source_title=detail.title,
                        source_published_at=detail.published_at,
                        source_hash_sha256=detail.hash_sha256,
                        source_file_kind=detail.file_kind,
                        storage_path=storage_path,
                        visits=visits,
                        resolved_places=post_resolved,
                        extractor_model=self.extractor_model,
                    )

                    quality = evaluate_batch(
                        batch,
                        parsed_rows=len(rows),
                        require_storage_path=self.require_storage_path and not self.config.dry_run,
                    )
                    quality_results.extend(quality)

                    if any(self._should_block(result) for result in quality):
                        break

                    if self.loader is not None:
                        _mark_stage(stats, "load_batch")
                        loaded_sources, loaded_places, loaded_visits = await self.loader.load(batch)
                        stats.loaded_sources += loaded_sources
                        stats.loaded_places += loaded_places
                        stats.loaded_visits += loaded_visits
            except PipelineConfigError as exc:
                if not isinstance(getattr(exc, "stats", None), PipelineStats):
                    setattr(exc, "stats", stats)
                raise
            finally:
                _mark_stage(stats, "close_crawler")
                await crawler.aclose()
        except PipelineConfigError as exc:
            if not isinstance(getattr(exc, "stats", None), PipelineStats):
                setattr(exc, "stats", stats)
            raise

        _mark_stage(stats, "complete")
        stats.places_seen = len(resolved_by_place_key)
        stats.kakao_matched_places = sum(
            1 for place in resolved_by_place_key.values() if place.matched
        )

        blocking_results = [result for result in quality_results if self._should_block(result)]
        if blocking_results:
            raise PipelineQualityError(_quality_gate_message(blocking_results), stats=stats)
        return stats

    def _should_block(self, result: QualityGateResult) -> bool:
        if result.ok:
            return False
        if self.config.quality_mode == "warn":
            return False
        return result.severity in {"fail", "quarantine"}


__all__ = ["ExpenseCrawler", "PipelineRunConfig", "PipelineRunner", "RowExtractor"]


def _mark_stage(stats: PipelineStats, stage: str) -> None:
    now = time.perf_counter()
    progress = PIPELINE_STAGE_PROGRESS.get()
    previous_stage = stats.current_stage
    previous_started_at = None
    if progress is not None:
        previous_started_at = progress.get("stage_started_at")

    if previous_stage:
        elapsed_ms = (
            max(0, int((now - previous_started_at) * 1000))
            if isinstance(previous_started_at, (int, float))
            else 0
        )
        stats.stage_elapsed_ms[previous_stage] = (
            stats.stage_elapsed_ms.get(previous_stage, 0) + elapsed_ms
        )

    stats.current_stage = stage
    stats.last_stage = stage
    if progress is not None:
        progress["current_stage"] = stage
        progress["last_stage"] = stage
        progress["stage_started_at"] = now
        progress["stage_elapsed_ms"] = dict(stats.stage_elapsed_ms)
        progress["stats"] = stats.model_dump()


def _quality_gate_message(results: list[QualityGateResult]) -> str:
    details = "; ".join(
        f"{result.code}: {result.message}" for result in results[:5]
    )
    if len(results) > 5:
        details = f"{details}; and {len(results) - 5} more"
    return f"quality gate failed: {details}"
