import argparse
import json
from datetime import date, datetime
from typing import Any

import pytest

from public_officer_pipeline import cli
from public_officer_pipeline.agencies import GYEONGGI_AGENCIES, SEOUL_AGENCIES
from public_officer_pipeline.pipeline.batch import LoadBatch
from public_officer_pipeline.models import (
    Agency,
    NormalizedVisit,
    ParsedExpenseRow,
    PlaceRaw,
    PostDetail,
    PostRef,
    ResolvedPlace,
)
from public_officer_pipeline.storage import SourceStorageError


def _sample_args() -> argparse.Namespace:
    return argparse.Namespace(
        since=date(2026, 5, 1),
        limit_pages=3,
        max_posts=10,
        skip_posts=0,
        dry_run=True,
        allow_deterministic_normalizer=False,
        allow_unmatched_places=False,
        allow_missing_r2=False,
        quality_mode="warn",
    )


def _fake_row_extractor(detail: PostDetail) -> list[ParsedExpenseRow]:
    _ = detail
    return [
        ParsedExpenseRow(
            department_name="총무과",
            used_at=datetime(2026, 5, 1, 12),
            place_text="테스트 식당",
            purpose="회의",
            amount=10000,
            user_text="테스트",
            payment_method="카드",
            expense_category="식대",
            raw_excerpt="테스트",
        )
    ]


class _FakeCrawler:
    def __init__(self, agency_id):
        self.agency_id = agency_id

    async def list_posts(self, since: date, limit_pages: int = 3) -> list[PostRef]:
        _ = since
        _ = limit_pages
        return [
            PostRef(
                agency_id=self.agency_id,
                url="https://example.com/expense/1",
                title="테스트 내역",
                published_at=date(2026, 5, 1),
                department_name="행정지원과",
                file_kind="html",
            )
        ]

    async def fetch_post(self, _post: PostRef) -> PostDetail:
        return PostDetail(
            agency_id=self.agency_id,
            url="https://example.com/expense/1",
            title="테스트 내역",
            published_at=date(2026, 5, 1),
            department_name="행정지원과",
            file_kind="html",
            html="테스트",
            content_bytes=None,
            fetched_at=datetime(2026, 5, 1, 12),
            hash_sha256="abcdef1234567890",
        )

    async def aclose(self) -> None:
        return None


class _FakeNormalizer:
    def __init__(self, *args, **kwargs) -> None:
        _ = args
        _ = kwargs

    async def normalize_rows(
        self,
        *,
        agency_id,
        source_url,
        source_title,
        source_published_at,
        source_hash_sha256,
        rows,
        **_kwargs,
    ) -> list[NormalizedVisit]:
        del rows
        return [
            NormalizedVisit(
                agency_id=agency_id,
                source_url=source_url,
                source_title=source_title,
                source_published_at=source_published_at,
                source_hash_sha256=source_hash_sha256,
                visit_date=date(2026, 5, 1),
                amount=10000,
                department_name="총무과",
                payment_method="카드",
                expense_category="식대",
                place_raw=PlaceRaw(name="테스트 식당", address_hint="서울시 영등포구"),
                raw_excerpt="테스트",
                confidence=1.0,
            )
        ]


class _FakeResolver:
    def __init__(self, *args, **kwargs) -> None:
        _ = args
        _ = kwargs

    async def resolve(self, _place_raw: PlaceRaw) -> ResolvedPlace:
        return ResolvedPlace(
            kakao_place_id="kakao-id",
            natural_key="kakao-id",
            name="테스트 식당",
            road_address="서울시 영등포구",
            matched=True,
        )


@pytest.mark.asyncio
async def test_run_supported_agency_blocks_adapter_required_before_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    called = {"flag": False}

    def explode(*args, **kwargs):  # pragma: no cover
        called["flag"] = True
        raise AssertionError("Crawler constructors must not be called for adapter_required")

    monkeypatch.setattr(cli, "CouncilAttachmentCrawler", explode)
    monkeypatch.setattr(cli, "GangnamExpenseCrawler", explode)
    monkeypatch.setattr(cli, "EstimateListCrawler", explode)
    monkeypatch.setattr(cli, "InlineExpenseTableCrawler", explode)

    result = await cli._run_supported_agency(_sample_args(), GYEONGGI_AGENCIES[0])
    output = json.loads(capsys.readouterr().err.strip())

    assert result == 2
    assert output["error"] == "adapter_required"
    assert not called["flag"]


@pytest.mark.asyncio
async def test_run_supported_agency_blocks_unknown_adapter_before_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    called = {"flag": False}

    def explode(*args, **kwargs):  # pragma: no cover
        called["flag"] = True
        raise AssertionError("Crawler constructors must not be called for unknown adapter")

    monkeypatch.setattr(cli, "CouncilAttachmentCrawler", explode)
    monkeypatch.setattr(cli, "GangnamExpenseCrawler", explode)
    monkeypatch.setattr(cli, "EstimateListCrawler", explode)
    monkeypatch.setattr(cli, "InlineExpenseTableCrawler", explode)

    result = await cli._run_supported_agency(
        _sample_args(),
        Agency(
            short_name="테스트",
            name="테스트",
            source_pattern={"adapter": "unknown_adapter"},
        ),
    )
    output = json.loads(capsys.readouterr().err.strip())

    assert result == 2
    assert output["error"] == "unsupported_adapter"
    assert output["adapter"] == "unknown_adapter"
    assert not called["flag"]


def test_find_agency_searches_full_capital_area_registry() -> None:
    assert any(agency.short_name == "강남구청" for agency in SEOUL_AGENCIES)
    assert any(agency.short_name == "경기도청" for agency in SEOUL_AGENCIES) is False
    assert any(cli._find_agency("경기도청") is not None for _ in (0,))


@pytest.mark.asyncio
async def test_run_crawler_stores_artifact_and_passes_storage_path_to_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agency = SEOUL_AGENCIES[0]
    load_calls = []

    class _FakeStorage:
        @classmethod
        def from_env(cls) -> "_FakeStorage":
            return cls()

        def put_artifact(self, _artifact) -> str:
            return "r2://officer-map-raw/test/2026-05/abcdef1234567890.csv"

    class _FakeLoader:
        async def load(self, batch: LoadBatch) -> tuple[int, int, int]:
            load_calls.append(batch)
            return (1, 1, 1)

    args = _sample_args()
    args.dry_run = False

    monkeypatch.setattr(cli, "R2SourceStorage", _FakeStorage)
    monkeypatch.setattr(cli, "PostgresLoader", _FakeLoader)
    monkeypatch.setattr(cli, "Normalizer", _FakeNormalizer)
    monkeypatch.setattr(cli, "KakaoResolver", _FakeResolver)

    result = await cli._run_crawler(args, agency, _FakeCrawler(agency.id), _fake_row_extractor)

    assert result == 0
    assert load_calls
    assert load_calls[0].storage_path == "r2://officer-map-raw/test/2026-05/abcdef1234567890.csv"


@pytest.mark.asyncio
async def test_run_crawler_allows_missing_r2_with_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agency = SEOUL_AGENCIES[0]
    load_calls = []

    class _BrokenR2:
        @classmethod
        def from_env(cls) -> "_BrokenR2":
            raise SourceStorageError("missing env")

    class _FakeLoader:
        async def load(self, batch: LoadBatch) -> tuple[int, int, int]:
            load_calls.append(batch)
            return (1, 1, 1)

    args = _sample_args()
    args.dry_run = False
    args.allow_missing_r2 = True

    monkeypatch.setattr(cli, "R2SourceStorage", _BrokenR2)
    monkeypatch.setattr(cli, "PostgresLoader", _FakeLoader)
    monkeypatch.setattr(cli, "Normalizer", _FakeNormalizer)
    monkeypatch.setattr(cli, "KakaoResolver", _FakeResolver)

    result = await cli._run_crawler(args, agency, _FakeCrawler(agency.id), _fake_row_extractor)

    assert result == 0
    assert load_calls
    assert load_calls[0].storage_path is None


@pytest.mark.asyncio
async def test_run_crawler_missing_r2_without_flag_fails_with_config_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    agency = SEOUL_AGENCIES[0]

    class _BrokenR2:
        @classmethod
        def from_env(cls) -> "_BrokenR2":
            raise SourceStorageError("missing env")

    args = _sample_args()
    args.dry_run = False
    monkeypatch.setattr(cli, "R2SourceStorage", _BrokenR2)

    result = await cli._run_crawler(args, agency, _FakeCrawler(agency.id), _fake_row_extractor)
    output = json.loads(capsys.readouterr().err.strip())

    assert result == 3
    assert output["error"] == "config_error"


@pytest.mark.asyncio
async def test_dry_run_does_not_attempt_r2_upload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agency = SEOUL_AGENCIES[0]
    upload_attempted = False

    class _BrokenR2:
        @classmethod
        def from_env(cls) -> "_BrokenR2":
            pytest.fail("dry-run should not initialize R2 source storage")

    class _FakeLoader:
        async def load(self, _batch: LoadBatch) -> tuple[int, int, int]:
            pytest.fail("loader should not be used in dry-run")

    args = _sample_args()
    args.dry_run = True

    class _TrackingNormalizer(_FakeNormalizer):
        async def normalize_rows(self, *args: Any, **kwargs: Any) -> list[NormalizedVisit]:
            nonlocal upload_attempted
            upload_attempted = True
            return await super().normalize_rows(*args, **kwargs)

    monkeypatch.setattr(cli, "R2SourceStorage", _BrokenR2)
    monkeypatch.setattr(cli, "PostgresLoader", _FakeLoader)
    monkeypatch.setattr(cli, "Normalizer", _TrackingNormalizer)
    monkeypatch.setattr(cli, "KakaoResolver", _FakeResolver)

    result = await cli._run_crawler(args, agency, _FakeCrawler(agency.id), _fake_row_extractor)

    assert result == 0
    assert upload_attempted is True
