from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from datetime import date
from typing import Literal, Protocol

from public_officer_pipeline.entity import KakaoResolver
from public_officer_pipeline.legal.visibility import LegalVisibilityError, validate_normalized_visits
from public_officer_pipeline.models import (
    Agency,
    NormalizedVisit,
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
    limit_pages: int
    max_posts: int
    skip_posts: int = 0
    dry_run: bool = False
    quality_mode: Literal["warn", "quarantine", "fail"] = "fail"


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
            posts = await crawler.list_posts(
                since=self.config.since,
                limit_pages=self.config.limit_pages,
            )
            stats.posts_seen = len(posts)

            for post in posts[self.config.skip_posts : self.config.skip_posts + self.config.max_posts]:
                detail = await crawler.fetch_post(post)
                stats.posts_fetched += 1

                storage_path = self.storage.put_artifact(detail)

                extracted_rows = self.row_extractor(detail)
                rows = [
                    row
                    for row in (
                        await extracted_rows
                        if inspect.isawaitable(extracted_rows)
                        else extracted_rows
                    )
                    if row.used_at.date() >= self.config.since
                ]
                stats.parsed_rows += len(rows)

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

                post_resolved: dict[str, ResolvedPlace] = {}
                for visit in visits:
                    key = place_resolution_key(visit.place_raw)
                    if key in resolved_by_place_key:
                        post_resolved[key] = resolved_by_place_key[key]
                        continue
                    resolved = await self.resolver.resolve(visit.place_raw)
                    resolved_by_place_key[key] = resolved
                    post_resolved[key] = resolved

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
                    loaded_sources, loaded_places, loaded_visits = await self.loader.load(batch)
                    stats.loaded_sources += loaded_sources
                    stats.loaded_places += loaded_places
                    stats.loaded_visits += loaded_visits

        finally:
            await crawler.aclose()

        stats.places_seen = len(resolved_by_place_key)
        stats.kakao_matched_places = sum(
            1 for place in resolved_by_place_key.values() if place.matched
        )

        if any(not result.ok for result in quality_results) and self.config.quality_mode != "warn":
            raise PipelineConfigError("quality gate failed")
        return stats

    def _should_block(self, result: QualityGateResult) -> bool:
        if result.ok:
            return False
        if self.config.quality_mode == "warn":
            return False
        return result.severity in {"fail", "quarantine"}


__all__ = ["ExpenseCrawler", "PipelineRunConfig", "PipelineRunner", "RowExtractor"]
