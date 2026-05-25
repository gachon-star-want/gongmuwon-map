from datetime import date, datetime
from typing import Any

import pytest

from public_officer_pipeline.models import (
    Agency,
    NormalizedVisit,
    ParsedExpenseRow,
    PlaceRaw,
    PostDetail,
    PostRef,
    PipelineConfigError,
    ResolvedPlace,
)
from public_officer_pipeline.pipeline.batch import LoadBatch, place_resolution_key
from public_officer_pipeline.pipeline.run import PipelineRunConfig, PipelineRunner


class _FakeCrawler:
    def __init__(self, posts: list[PostRef]) -> None:
        self.posts = posts
        self.calls: list[str] = []

    async def list_posts(self, since: date, limit_pages: int = 3) -> list[PostRef]:
        self.calls.append(f"list_posts:{since}:{limit_pages}")
        return self.posts

    async def fetch_post(self, ref: PostRef) -> PostDetail:
        self.calls.append(f"fetch_post:{ref.url}")
        return PostDetail(
            agency_id=ref.agency_id,
            url=ref.url,
            title=ref.title,
            published_at=date(2026, 5, 1),
            department_name=ref.department_name,
            file_kind=ref.file_kind,
            html="content",
            fetched_at=datetime(2026, 5, 1, 12),
            hash_sha256="hash-1234",
        )

    async def aclose(self) -> None:
        self.calls.append("aclose")


class _FakeStorage:
    def put_artifact(self, _detail: PostDetail) -> str:
        return "memory://artifact"


class _FakeResolver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def resolve(self, place_raw: PlaceRaw) -> ResolvedPlace:
        self.calls.append(place_raw.model_dump_json())
        return ResolvedPlace(
            kakao_place_id="kakao-id",
            natural_key="kakao-id",
            name=place_raw.name,
            road_address=place_raw.address_hint,
            road_address_part="서울 중구",
            latitude=37.5665,
            longitude=126.978,
            matched=True,
        )


class _FakeLoader:
    def __init__(self) -> None:
        self.calls: list[LoadBatch] = []

    async def load(self, batch: LoadBatch) -> tuple[int, int, int]:
        self.calls.append(batch)
        return (1, len(batch.resolved_places), len(batch.visits))


def _visit(*, name: str, confidence: float = 0.9) -> NormalizedVisit:
    return NormalizedVisit(
        agency_id=Agency().id,
        source_url="https://example.com/expense/1",
        source_title="title",
        source_published_at=date(2026, 5, 1),
        source_hash_sha256="hash-1234",
        visit_date=date(2026, 5, 1),
        amount=10000,
        department_name="총무과",
        place_raw=PlaceRaw(name=name, address_hint="서울시 중구"),
        raw_excerpt="row",
        confidence=confidence,
    )


class _FakeNormalizer:
    def __init__(self, visits: list[NormalizedVisit]) -> None:
        self.visits = visits
        self.calls: list[str] = []

    async def normalize_rows(
        self,
        *,
        agency_id: Any,
        source_url: Any,
        source_title: Any,
        source_hash_sha256: Any,
        rows: list[ParsedExpenseRow],
        **_kwargs: Any,
    ) -> list[NormalizedVisit]:
        self.calls.append(f"normalize:{agency_id}:{len(rows)}")
        return self.visits


def _row_extractor(*, rows: int) -> Any:
    def _extract(_detail: PostDetail) -> list[ParsedExpenseRow]:
        return [
            ParsedExpenseRow(
                department_name="총무과",
                used_at=datetime(2026, 5, 1, 12),
                place_text="테스트",
                purpose="회의",
                amount=10000,
                user_text="테스트",
                payment_method="카드",
                expense_category="식대",
                raw_excerpt="테스트",
            )
            for _ in range(rows)
        ]

    def _extract_with_conf(_detail: PostDetail) -> list[ParsedExpenseRow]:
        parsed = _extract(_detail)
        return parsed

    return _extract_with_conf


def _agency() -> Agency:
    return Agency()


def _run_config(**kwargs: Any) -> PipelineRunConfig:
    base = {
        "since": date(2026, 5, 1),
        "limit_pages": 3,
        "max_posts": 10,
        "skip_posts": 0,
        "dry_run": False,
    }
    base.update(kwargs)
    return PipelineRunConfig(**base)


@pytest.mark.asyncio
async def test_run_sequence_invokes_all_stages_in_order() -> None:
    agency = _agency()
    posts = [
        PostRef(
            agency_id=agency.id,
            url="https://example.com/expense/1",
            title="내역1",
            published_at=date(2026, 5, 1),
            department_name="총무과",
        )
    ]
    crawler = _FakeCrawler(posts)
    extractor_calls: list[str] = []

    def extract_rows(detail: PostDetail) -> list[ParsedExpenseRow]:
        _ = detail
        extractor_calls.append(f"extract:{detail.url}")
        return _row_extractor(rows=1)(detail)

    normalizer = _FakeNormalizer([_visit(name="식당")])
    resolver = _FakeResolver()
    loader = _FakeLoader()

    runner = PipelineRunner(
        config=_run_config(),
        normalizer=normalizer,
        resolver=resolver,
        storage=_FakeStorage(),
        row_extractor=extract_rows,
        loader=loader,
    )

    await runner.run_agency(agency, crawler)

    assert crawler.calls[0].startswith("list_posts")
    assert crawler.calls[1].startswith("fetch_post")
    assert crawler.calls[2] == "aclose"
    assert normalizer.calls == ["normalize:00000000-0000-0000-0000-000000000001:1"]
    assert len(resolver.calls) == 1
    assert extractor_calls == ["extract:https://example.com/expense/1"]
    assert len(loader.calls) == 1


@pytest.mark.asyncio
async def test_run_respects_skip_posts_and_max_posts() -> None:
    agency = _agency()
    posts = [
        PostRef(
            agency_id=agency.id,
            url=f"https://example.com/expense/{i}",
            title="내역",
            published_at=date(2026, 5, 1),
            department_name="총무과",
        )
        for i in range(3)
    ]
    crawler = _FakeCrawler(posts)
    extractor_calls: list[str] = []

    def extract_rows(detail: PostDetail) -> list[ParsedExpenseRow]:
        extractor_calls.append(detail.url)
        return _row_extractor(rows=1)(detail)

    normalizer = _FakeNormalizer([_visit(name="식당")])
    resolver = _FakeResolver()
    loader = _FakeLoader()

    runner = PipelineRunner(
        config=_run_config(skip_posts=1, max_posts=1),
        normalizer=normalizer,
        resolver=resolver,
        storage=_FakeStorage(),
        row_extractor=extract_rows,
        loader=loader,
    )

    await runner.run_agency(agency, crawler)

    assert len([call for call in crawler.calls if call.startswith("fetch_post")]) == 1
    assert extractor_calls == ["https://example.com/expense/1"]
    assert len(loader.calls) == 1
    assert len(resolver.calls) == 1


@pytest.mark.asyncio
async def test_run_dry_run_does_not_call_loader() -> None:
    agency = _agency()
    crawler = _FakeCrawler(
        [
            PostRef(
                agency_id=agency.id,
                url="https://example.com/expense/1",
                title="내역",
                published_at=date(2026, 5, 1),
                department_name="총무과",
            )
        ]
    )
    normalizer = _FakeNormalizer([_visit(name="식당")])
    resolver = _FakeResolver()

    runner = PipelineRunner(
        config=_run_config(dry_run=True),
        normalizer=normalizer,
        resolver=resolver,
        storage=_FakeStorage(),
        row_extractor=lambda detail: _row_extractor(rows=1)(detail),
        loader=None,
    )

    stats = await runner.run_agency(agency, crawler)

    assert stats.loaded_sources == 0
    assert stats.loaded_places == 0
    assert stats.loaded_visits == 0


@pytest.mark.asyncio
async def test_quality_warn_mode_loads_non_compliant_batch() -> None:
    agency = _agency()
    crawler = _FakeCrawler(
        [
            PostRef(
                agency_id=agency.id,
                url="https://example.com/expense/1",
                title="내역",
                published_at=date(2026, 5, 1),
                department_name="총무과",
            )
        ]
    )
    normalizer = _FakeNormalizer([_visit(name="식당", confidence=0.4)])
    resolver = _FakeResolver()
    loader = _FakeLoader()

    runner = PipelineRunner(
        config=_run_config(quality_mode="warn"),
        normalizer=normalizer,
        resolver=resolver,
        storage=_FakeStorage(),
        row_extractor=_row_extractor(rows=1),
        loader=loader,
    )

    await runner.run_agency(agency, crawler)

    assert len(loader.calls) == 1
    assert loader.calls[0].visits[0].confidence == 0.4


@pytest.mark.asyncio
async def test_quality_fail_mode_stops_before_load() -> None:
    agency = _agency()
    crawler = _FakeCrawler(
        [
            PostRef(
                agency_id=agency.id,
                url="https://example.com/expense/1",
                title="내역",
                published_at=date(2026, 5, 1),
                department_name="총무과",
            )
        ]
    )
    normalizer = _FakeNormalizer([_visit(name="식당", confidence=0.4)])
    resolver = _FakeResolver()
    loader = _FakeLoader()

    runner = PipelineRunner(
        config=_run_config(quality_mode="fail"),
        normalizer=normalizer,
        resolver=resolver,
        storage=_FakeStorage(),
        row_extractor=_row_extractor(rows=1),
        loader=loader,
    )

    with pytest.raises(PipelineConfigError):
        await runner.run_agency(agency, crawler)

    assert not loader.calls


@pytest.mark.asyncio
async def test_loader_receives_resolved_place_keys_matching_place_resolution_key() -> None:
    agency = _agency()
    crawler = _FakeCrawler(
        [
            PostRef(
                agency_id=agency.id,
                url="https://example.com/expense/1",
                title="내역",
                published_at=date(2026, 5, 1),
                department_name="총무과",
            )
        ]
    )
    normalizer = _FakeNormalizer([
        _visit(name="식당A"),
        _visit(name="식당A"),
    ])
    resolver = _FakeResolver()
    loader = _FakeLoader()

    runner = PipelineRunner(
        config=_run_config(),
        normalizer=normalizer,
        resolver=resolver,
        storage=_FakeStorage(),
        row_extractor=_row_extractor(rows=2),
        loader=loader,
    )

    await runner.run_agency(agency, crawler)

    assert len(loader.calls) == 1
    batch = loader.calls[0]
    expected_key = place_resolution_key(_visit(name="식당A").place_raw)
    assert set(batch.resolved_places.keys()) == {expected_key}
    assert len(batch.visits) == 2
    assert len(resolver.calls) == 1
    assert batch.resolved_places[expected_key].kakao_place_id == "kakao-id"
