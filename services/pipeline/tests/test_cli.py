import argparse
import asyncio
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
        row_since=None,
        limit_pages=3,
        max_posts=10,
        skip_posts=0,
        dry_run=True,
        allow_deterministic_normalizer=False,
        allow_unmatched_places=False,
        allow_missing_r2=False,
        quality_mode="warn",
        production_gate_report=None,
    )


def _sample_batch_args() -> argparse.Namespace:
    args = _sample_args()
    args.scope = "incheon"
    args.agency = []
    args.concurrency = 3
    args.max_attempts = 5
    args.retry_delay_seconds = 0.0
    args.agency_timeout_seconds = 0.0
    args.confirm_production_write = False
    args.write_target = "staging"
    args.allow_production_write = False
    return args


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


def test_find_agency_searches_full_nationwide_registry() -> None:
    assert any(agency.short_name == "강남구청" for agency in SEOUL_AGENCIES)
    assert any(agency.short_name == "경기도청" for agency in SEOUL_AGENCIES) is False
    assert any(cli._find_agency("경기도청") is not None for _ in (0,))
    assert cli._find_agency("세종시청") is not None
    assert cli._find_agency("중구청") is None

    agency, error = cli._resolve_agency("중구청")
    assert agency is None
    assert error["error"] == "ambiguous_agency"
    assert {match["parent_region"] for match in error["matches"]} == {
        "서울특별시",
        "부산광역시",
        "대구광역시",
        "대전광역시",
        "울산광역시",
        "인천광역시",
    }


def test_agencies_for_scope_returns_expected_registry_slices() -> None:
    assert len(cli._agencies_for_scope("seoul")) == 52
    assert len(cli._agencies_for_scope("gyeonggi")) == 64
    assert len(cli._agencies_for_scope("incheon")) == 22
    assert len(cli._agencies_for_scope("capital-area")) == 138
    assert len(cli._agencies_for_scope("gyeongsang")) == 150
    assert len(cli._agencies_for_scope("jeolla")) == 88
    assert len(cli._agencies_for_scope("chungcheong")) == 70
    assert len(cli._agencies_for_scope("gangwon")) == 38
    assert len(cli._agencies_for_scope("jeju")) == 4
    assert len(cli._agencies_for_scope("non-capital")) == 350
    assert len(cli._agencies_for_scope("nationwide")) == 2202


def test_print_source_registry_reports_capital_area_verification_state(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = argparse.Namespace(scope="capital-area", format="json", summary_only=False)

    result = cli._print_source_registry(args)
    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["summary"]["total"] == 138
    assert output["summary"]["verified_in_code"] == 131
    assert output["summary"]["pending"] == 0
    assert output["summary"]["legal_hold"] == 7
    assert output["summary"]["source_not_found"] == 0
    assert output["summary"]["adapter_hold"] == 0
    assert output["summary"]["invalid_source_pattern"] == 0


def test_print_source_registry_reports_nationwide_verification_state(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = argparse.Namespace(scope="nationwide", format="json", summary_only=False)

    result = cli._print_source_registry(args)
    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["summary"]["total"] == 2202
    assert output["summary"]["verified_in_code"] == 541
    assert output["summary"]["pending"] == 43
    assert output["summary"]["legal_hold"] == 107
    assert output["summary"]["source_not_found"] == 109
    assert output["summary"]["no_recent_data"] == 1192
    assert output["summary"]["pdf_vision_hold"] == 30
    assert output["summary"]["adapter_hold"] == 180
    assert output["summary"]["invalid_source_pattern"] == 0
    assert output["summary"]["priority_group_counts"]["p1"]["total"] == 488
    assert output["summary"]["priority_group_counts"]["p1"]["verified_in_code"] == 193
    assert output["summary"]["priority_group_counts"]["p1"]["legal_hold"] == 107
    assert output["summary"]["priority_group_counts"]["p2"]["total"] == 60
    assert output["summary"]["priority_group_counts"]["p2"]["verified_in_code"] == 1
    assert output["summary"]["priority_group_counts"]["p2"]["source_not_found"] == 32
    assert output["summary"]["priority_group_counts"]["p2"]["pdf_vision_hold"] == 2
    assert output["summary"]["priority_group_counts"]["p2"]["adapter_hold"] == 25
    assert output["summary"]["priority_group_counts"]["p3"]["total"] == 342
    assert output["summary"]["priority_group_counts"]["p3"]["verified_in_code"] == 6
    assert output["summary"]["priority_group_counts"]["p3"]["pending"] == 0
    assert output["summary"]["priority_group_counts"]["p3"]["no_recent_data"] == 288
    assert output["summary"]["priority_group_counts"]["p3"]["pdf_vision_hold"] == 8
    assert output["summary"]["priority_group_counts"]["p3"]["adapter_hold"] == 40
    assert output["summary"]["priority_group_counts"]["p4"]["total"] == 1312
    assert output["summary"]["priority_group_counts"]["p4"]["verified_in_code"] == 341
    assert output["summary"]["priority_group_counts"]["p4"]["no_recent_data"] == 903
    assert output["summary"]["priority_group_counts"]["p4"]["adapter_hold"] == 68


def test_print_source_registry_summary_only_omits_entries(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = argparse.Namespace(scope="nationwide", format="json", summary_only=True)

    result = cli._print_source_registry(args)
    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["summary"]["total"] == 2202
    assert output["summary"]["verified_in_code"] == 541
    assert "entries" not in output


def test_run_agency_requires_staging_database_url_for_single_non_dry_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("DATABASE_URL_STAGING", raising=False)
    monkeypatch.delenv("STAGING_DATABASE_URL", raising=False)

    result = cli.main(["run-agency", "서울시청"])
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "staging_database_url_required"


@pytest.mark.parametrize(
    "command",
    [
        ["apply-schema"],
        ["seed-agencies"],
        ["refresh-views"],
    ],
)
def test_db_write_commands_require_staging_database_url_by_default(
    command: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("DATABASE_URL_STAGING", raising=False)
    monkeypatch.delenv("STAGING_DATABASE_URL", raising=False)

    result = cli.main(command)
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "staging_database_url_required"


def test_apply_schema_uses_staging_database_url_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []

    def fake_apply_schema(*, database_url: str | None = None, migration_path: Any = None) -> None:
        calls.append((database_url, migration_path))

    monkeypatch.setenv("DATABASE_URL_STAGING", "postgresql://staging.example/db")
    for name in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(cli, "apply_schema", fake_apply_schema)

    result = cli.main(["apply-schema"])
    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert calls == [("postgresql://staging.example/db", cli.Path("supabase/migrations/20260523235106_initial.sql"))]
    assert output["write_target"] == "staging"


def test_apply_schema_accepts_staging_database_url_alias(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []

    def fake_apply_schema(*, database_url: str | None = None, migration_path: Any = None) -> None:
        calls.append((database_url, migration_path))

    monkeypatch.delenv("DATABASE_URL_STAGING", raising=False)
    monkeypatch.setenv("STAGING_DATABASE_URL", "postgresql://staging-alias.example/db")
    monkeypatch.setattr(cli, "apply_schema", fake_apply_schema)

    result = cli.main(["apply-schema"])
    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert calls == [
        (
            "postgresql://staging-alias.example/db",
            cli.Path("supabase/migrations/20260523235106_initial.sql"),
        )
    ]
    assert output["write_target"] == "staging"


def test_seed_agencies_uses_staging_database_url_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    loader_urls = []

    class _FakeLoader:
        def __init__(self, *, database_url: str | None = None) -> None:
            loader_urls.append(database_url)

        async def seed_agencies(self, agencies: list[Agency]) -> int:
            return len(agencies)

    monkeypatch.setenv("DATABASE_URL_STAGING", "postgresql://staging.example/db")
    for name in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(cli, "PostgresLoader", _FakeLoader)

    result = cli.main(["seed-agencies"])
    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert loader_urls == ["postgresql://staging.example/db"]
    assert output["scope"] == "seoul"
    assert output["write_target"] == "staging"


def test_refresh_views_uses_staging_database_url_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []

    def fake_refresh_materialized_views(*, database_url: str | None = None) -> None:
        calls.append(database_url)

    monkeypatch.setenv("DATABASE_URL_STAGING", "postgresql://staging.example/db")
    for name in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(cli, "refresh_materialized_views", fake_refresh_materialized_views)

    result = cli.main(["refresh-views"])
    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert calls == ["postgresql://staging.example/db"]
    assert output["write_target"] == "staging"


@pytest.mark.asyncio
async def test_run_crawler_stores_artifact_and_passes_storage_path_to_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agency = SEOUL_AGENCIES[0]
    load_calls = []

    class _FakeStorage:
        @classmethod
        def from_env(cls, **_kwargs: Any) -> "_FakeStorage":
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
        def from_env(cls, **_kwargs: Any) -> "_BrokenR2":
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
        def from_env(cls, **_kwargs: Any) -> "_BrokenR2":
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
        def from_env(cls, **_kwargs: Any) -> "_BrokenR2":
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


@pytest.mark.asyncio
async def test_run_agencies_allows_non_dry_run_staging_without_production_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    called = []

    async def fake_run_supported_agency_result(
        _args: argparse.Namespace, agency: Agency
    ) -> tuple[int, dict[str, object]]:
        called.append(agency.short_name)
        return 0, {}

    monkeypatch.setattr(cli, "_run_supported_agency_result", fake_run_supported_agency_result)
    args = _sample_batch_args()
    args.agency = ["서울시청"]
    args.dry_run = False
    args.write_target = "staging"
    monkeypatch.setenv("DATABASE_URL_STAGING", "postgresql://staging.example/db")
    monkeypatch.setenv("R2_ACCOUNT_ID", "account")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "access")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("R2_BUCKET", "bucket")

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert called == ["서울시청"]
    assert output["summary"]["dry_run"] is False
    assert output["summary"]["write_target"] == "staging"


@pytest.mark.asyncio
async def test_run_agencies_requires_staging_database_url_for_staging_writes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("DATABASE_URL_STAGING", raising=False)
    monkeypatch.delenv("STAGING_DATABASE_URL", raising=False)
    args = _sample_batch_args()
    args.agency = ["서울시청"]
    args.dry_run = False
    args.write_target = "staging"

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "staging_database_url_required"


@pytest.mark.asyncio
async def test_run_agencies_requires_r2_for_staging_writes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DATABASE_URL_STAGING", "postgresql://staging.example/db")
    for name in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"):
        monkeypatch.delenv(name, raising=False)
    args = _sample_batch_args()
    args.agency = ["서울시청"]
    args.dry_run = False
    args.write_target = "staging"

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "staging_r2_required"
    assert output["missing"] == [
        "R2_ACCOUNT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET",
    ]


@pytest.mark.asyncio
async def test_run_agencies_accepts_staging_r2_env_aliases(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def fake_run_supported_agency_result(
        _args: argparse.Namespace, _agency: Agency
    ) -> tuple[int, dict[str, object]]:
        return 0, {}

    monkeypatch.setattr(cli, "_run_supported_agency_result", fake_run_supported_agency_result)
    monkeypatch.setenv("DATABASE_URL_STAGING", "postgresql://staging.example/db")
    for name in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("R2_STAGING_ACCOUNT_ID", "account")
    monkeypatch.setenv("R2_STAGING_ACCESS_KEY_ID", "access")
    monkeypatch.setenv("R2_STAGING_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("R2_STAGING_BUCKET", "bucket")
    args = _sample_batch_args()
    args.agency = ["서울시청"]
    args.dry_run = False
    args.write_target = "staging"

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["summary"]["success"] == 1


@pytest.mark.asyncio
async def test_run_agencies_requires_confirmation_for_production_writes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = _sample_batch_args()
    args.dry_run = False
    args.write_target = "production"
    args.confirm_production_write = False

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "confirmation_required"


@pytest.mark.asyncio
async def test_run_agencies_requires_second_opt_in_for_production_writes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = _sample_batch_args()
    args.dry_run = False
    args.write_target = "production"
    args.confirm_production_write = True
    args.allow_production_write = False

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "production_write_opt_in_required"


@pytest.mark.asyncio
async def test_run_agencies_requires_gate_report_for_all_production_writes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = _sample_batch_args()
    args.dry_run = False
    args.write_target = "production"
    args.confirm_production_write = True
    args.allow_production_write = True
    args.scope = "seoul"

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "production_gate_report_required"


@pytest.mark.asyncio
async def test_run_agencies_rejects_not_ready_gate_report_for_production_writes(
    tmp_path: Any,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = tmp_path / "nationwide-verification-report.md"
    report.write_text("서비스 주입 판정: production 주입 불가", encoding="utf-8")

    args = _sample_batch_args()
    args.dry_run = False
    args.write_target = "production"
    args.confirm_production_write = True
    args.allow_production_write = True
    args.scope = "nationwide"
    args.production_gate_report = report

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "production_gate_report_not_ready"


def test_single_agency_production_write_requires_gate_report(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = cli.main(
        [
            "run-agency",
            "서울시청",
            "--write-target",
            "production",
            "--confirm-production-write",
            "--allow-production-write",
        ]
    )
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "production_gate_report_required"


def test_apply_schema_production_write_requires_gate_report(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = cli.main(
        [
            "apply-schema",
            "--write-target",
            "production",
            "--confirm-production-write",
            "--allow-production-write",
        ]
    )
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "production_gate_report_required"


@pytest.mark.asyncio
async def test_run_agencies_rejects_unsafe_concurrency(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = _sample_batch_args()
    args.concurrency = 21

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "invalid_concurrency"


@pytest.mark.asyncio
async def test_run_agencies_summarizes_adapter_required_without_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    called = []

    async def fake_run_supported_agency_result(
        _args: argparse.Namespace, agency: Agency
    ) -> tuple[int, dict[str, object]]:
        called.append(agency.short_name)
        return 2, {"error": "adapter_required"}

    monkeypatch.setattr(cli, "_run_supported_agency_result", fake_run_supported_agency_result)
    args = _sample_batch_args()
    args.agency = ["경기도청"]
    args.dry_run = True
    args.concurrency = 5

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert called == []
    assert output["summary"]["total"] == 1
    assert output["summary"]["adapter_required"] == 1


@pytest.mark.asyncio
async def test_run_agencies_accepts_explicit_subset(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    called = []

    async def fake_run_supported_agency_result(
        _args: argparse.Namespace, agency: Agency
    ) -> tuple[int, dict[str, object]]:
        called.append(agency.short_name)
        return 0, {}

    monkeypatch.setattr(cli, "_run_supported_agency_result", fake_run_supported_agency_result)
    args = _sample_batch_args()
    args.agency = ["서울시청", "서울시의회"]
    args.dry_run = True

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert called == ["서울시청", "서울시의회"]
    assert output["summary"]["total"] == 2
    assert output["summary"]["success"] == 2


@pytest.mark.asyncio
async def test_run_agencies_isolates_single_agency_failures(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def fake_run_supported_agency_result(
        _args: argparse.Namespace, agency: Agency
    ) -> tuple[int, dict[str, object]]:
        if agency.short_name == "서울시청":
            raise RuntimeError("boom")
        return 0, {}

    monkeypatch.setattr(cli, "_run_supported_agency_result", fake_run_supported_agency_result)
    args = _sample_batch_args()
    args.agency = ["서울시청", "서울시의회"]
    args.dry_run = True

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().out)

    assert result == 3
    assert output["summary"]["total"] == 2
    assert output["summary"]["success"] == 1
    assert output["summary"]["failed"] == 1
    failed = next(item for item in output["results"] if item["result"] == "failed")
    assert failed["short_name"] == "서울시청"
    assert failed["error"] == "boom"


@pytest.mark.asyncio
async def test_run_agencies_records_per_agency_timeout(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def fake_run_supported_agency_result(
        _args: argparse.Namespace, _agency: Agency
    ) -> tuple[int, dict[str, object]]:
        await asyncio.sleep(1)
        return 0, {}

    monkeypatch.setattr(cli, "_run_supported_agency_result", fake_run_supported_agency_result)
    args = _sample_batch_args()
    args.agency = ["서울시청"]
    args.dry_run = True
    args.agency_timeout_seconds = 0.01

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().out)

    assert result == 3
    assert output["summary"]["failed"] == 1
    assert output["summary"]["failure_reasons"] == {"timeout": 1}
    assert output["summary"]["agency_timeout_seconds"] == 0.01
    item = output["results"][0]
    assert item["failure_reason"] == "timeout"
    assert item["attempt_count"] == 1
    assert item["attempts"][0]["attempt"] == 1
    assert item["current_stage"] == "start_attempt"
    assert item["timeout_stage"] == "start_attempt"
    assert item["last_stage"] == "start_attempt"
    assert item["stage_elapsed_ms"] == {}
    assert "timed out after 0.01 seconds" in item["error"]


@pytest.mark.asyncio
async def test_run_agencies_timeout_stage_prefers_overrun_stage(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def fake_run_supported_agency_result(
        _args: argparse.Namespace, _agency: Agency
    ) -> tuple[int, dict[str, object]]:
        progress = cli.PIPELINE_STAGE_PROGRESS.get()
        assert progress is not None
        progress["current_stage"] = "close_crawler"
        progress["last_stage"] = "close_crawler"
        progress["stage_elapsed_ms"] = {"extract_rows": 25, "close_crawler": 1}
        progress["stats"] = {"posts_seen": 3, "posts_fetched": 1, "raw_parsed_rows": 2}
        await asyncio.sleep(1)
        return 0, {}

    monkeypatch.setattr(cli, "_run_supported_agency_result", fake_run_supported_agency_result)
    args = _sample_batch_args()
    args.agency = ["서울시청"]
    args.dry_run = True
    args.agency_timeout_seconds = 0.01

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().out)
    item = output["results"][0]

    assert result == 3
    assert item["current_stage"] == "close_crawler"
    assert item["last_stage"] == "close_crawler"
    assert item["timeout_stage"] == "extract_rows"
    assert item["stage_elapsed_ms"] == {"extract_rows": 25, "close_crawler": 1}
    assert item["posts_seen"] == 3
    assert item["posts_fetched"] == 1
    assert item["raw_parsed_rows"] == 2


@pytest.mark.asyncio
async def test_run_agencies_bounds_retry_delay_by_deadline(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []

    async def fake_run_supported_agency_result(
        _args: argparse.Namespace, agency: Agency
    ) -> tuple[int, dict[str, object]]:
        calls.append(agency.short_name)
        return 3, {"error": "config_error", "message": "download timeout"}

    monkeypatch.setattr(cli, "_run_supported_agency_result", fake_run_supported_agency_result)
    args = _sample_batch_args()
    args.agency = ["서울시청"]
    args.dry_run = True
    args.max_attempts = 5
    args.retry_delay_seconds = 1
    args.agency_timeout_seconds = 0.01

    started_at = asyncio.get_running_loop().time()
    result = await cli._run_agencies(args)
    elapsed = asyncio.get_running_loop().time() - started_at
    output = json.loads(capsys.readouterr().out)
    item = output["results"][0]

    assert result == 3
    assert elapsed < 0.5
    assert calls == ["서울시청"]
    assert item["attempt_count"] == 2
    assert item["failure_reason"] == "timeout"


@pytest.mark.asyncio
async def test_run_agencies_retries_retryable_failures_and_records_stats(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []

    async def fake_run_supported_agency_result(
        _args: argparse.Namespace, agency: Agency
    ) -> tuple[int, dict[str, object]]:
        calls.append(agency.short_name)
        if len(calls) < 3:
            return 3, {"error": "config_error", "message": "download timeout"}
        return 0, {
            "posts_seen": 2,
            "posts_fetched": 2,
            "parsed_rows": 4,
            "normalized_visits": 4,
            "places_seen": 3,
            "kakao_matched_places": 2,
            "loaded_sources": 0,
            "loaded_places": 0,
            "loaded_visits": 0,
            "skipped_invalid_places": 1,
            "kakao_match_rate": 2 / 3,
        }

    monkeypatch.setattr(cli, "_run_supported_agency_result", fake_run_supported_agency_result)
    args = _sample_batch_args()
    args.agency = ["서울시청"]
    args.dry_run = True
    args.max_attempts = 3

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert calls == ["서울시청", "서울시청", "서울시청"]
    assert output["summary"]["success"] == 1
    assert output["summary"]["parsed_rows"] == 4
    assert output["summary"]["skipped_invalid_places"] == 1
    item = output["results"][0]
    assert item["attempt_count"] == 3
    assert item["attempts"][0]["failure_reason"] == "auth_js_download"
    assert item["failure_reason"] is None
    assert item["parsed_rows"] == 4


@pytest.mark.asyncio
async def test_run_agencies_does_not_retry_deterministic_quality_failures(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []

    async def fake_run_supported_agency_result(
        _args: argparse.Namespace, agency: Agency
    ) -> tuple[int, dict[str, object]]:
        calls.append(agency.short_name)
        return 3, {"error": "config_error", "message": "quality gate failed: missing_coordinates"}

    monkeypatch.setattr(cli, "_run_supported_agency_result", fake_run_supported_agency_result)
    args = _sample_batch_args()
    args.agency = ["서울시청"]
    args.dry_run = True
    args.max_attempts = 5

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().out)
    item = output["results"][0]

    assert result == 3
    assert calls == ["서울시청"]
    assert item["attempt_count"] == 1
    assert item["failure_reason"] == "kakao_resolution"


@pytest.mark.asyncio
async def test_run_agencies_records_failure_reason_after_five_attempts(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []

    async def fake_run_supported_agency_result(
        _args: argparse.Namespace, agency: Agency
    ) -> tuple[int, dict[str, object]]:
        calls.append(agency.short_name)
        return 3, {
            "error": "config_error",
            "message": "At least one LLM API key is required for scanned PDF vision extraction",
        }

    monkeypatch.setattr(cli, "_run_supported_agency_result", fake_run_supported_agency_result)
    args = _sample_batch_args()
    args.agency = ["서울시청"]
    args.dry_run = True
    args.max_attempts = 5

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().out)

    assert result == 3
    assert calls == ["서울시청"] * 5
    assert output["summary"]["config_error"] == 1
    assert output["summary"]["failure_reasons"] == {"llm_extraction_failure": 1}
    item = output["results"][0]
    assert item["attempt_count"] == 5
    assert item["failure_reason"] == "llm_extraction_failure"
    assert all(attempt["failure_reason"] == "llm_extraction_failure" for attempt in item["attempts"])


@pytest.mark.asyncio
async def test_run_agencies_summarizes_stats_from_quality_failures(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def fake_run_supported_agency_result(
        _args: argparse.Namespace, _agency: Agency
    ) -> tuple[int, dict[str, object]]:
        return 3, {
            "error": "config_error",
            "message": "quality gate failed: missing_coordinates",
            "posts_seen": 11,
            "posts_fetched": 2,
            "raw_parsed_rows": 21,
            "parsed_rows": 21,
            "normalized_visits": 21,
            "places_seen": 17,
            "kakao_matched_places": 15,
            "kakao_match_rate": 15 / 17,
        }

    monkeypatch.setattr(cli, "_run_supported_agency_result", fake_run_supported_agency_result)
    args = _sample_batch_args()
    args.agency = ["서울시청"]
    args.dry_run = True
    args.max_attempts = 1

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().out)

    assert result == 3
    assert output["summary"]["raw_parsed_rows"] == 21
    assert output["summary"]["parsed_rows"] == 21
    assert output["summary"]["places_seen"] == 17
    item = output["results"][0]
    assert item["raw_parsed_rows"] == 21
    assert item["kakao_match_rate"] == 15 / 17


@pytest.mark.asyncio
async def test_run_agencies_rejects_ambiguous_short_name(capsys: pytest.CaptureFixture[str]) -> None:
    args = _sample_batch_args()
    args.agency = ["중구청"]
    args.dry_run = True

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "ambiguous_agency"
    assert {match["parent_region"] for match in output["matches"]} == {
        "서울특별시",
        "부산광역시",
        "대구광역시",
        "대전광역시",
        "울산광역시",
        "인천광역시",
    }


@pytest.mark.asyncio
async def test_run_agencies_treats_unknown_adapter_as_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    agency = Agency(short_name="테스트", name="테스트", source_pattern={"adapter": "unknown_adapter"})
    monkeypatch.setattr(cli, "_agencies_for_scope", lambda _scope: [agency])
    args = _sample_batch_args()
    args.dry_run = True

    result = await cli._run_agencies(args)
    streams = capsys.readouterr()
    output = json.loads(streams.out)

    assert result == 3
    assert output["summary"]["ok"] is False
    assert output["summary"]["unsupported"] == 1


@pytest.mark.asyncio
async def test_run_agencies_rejects_unsafe_max_attempts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = _sample_batch_args()
    args.max_attempts = 6

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "invalid_max_attempts"


@pytest.mark.asyncio
async def test_run_agencies_rejects_negative_agency_timeout(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = _sample_batch_args()
    args.agency_timeout_seconds = -1

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().err)

    assert result == 2
    assert output["error"] == "invalid_agency_timeout"


@pytest.mark.asyncio
async def test_run_agencies_dry_run_skips_production_write_guards(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    called = []

    async def fake_run_supported_agency_result(
        _args: argparse.Namespace, agency: Agency
    ) -> tuple[int, dict[str, object]]:
        called.append(agency.short_name)
        return 0, {}

    monkeypatch.setattr(cli, "_run_supported_agency_result", fake_run_supported_agency_result)
    args = _sample_batch_args()
    args.agency = ["서울시청"]
    args.dry_run = True
    args.write_target = "production"
    args.confirm_production_write = False
    args.allow_production_write = False

    result = await cli._run_agencies(args)
    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert called == ["서울시청"]
    assert output["summary"]["dry_run"] is True


@pytest.mark.asyncio
async def test_run_crawler_uses_staging_database_url_for_batch_staging_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agency = SEOUL_AGENCIES[0]
    loader_urls = []

    class _FakeLoader:
        def __init__(self, *, database_url: str | None = None) -> None:
            loader_urls.append(database_url)

        async def load(self, batch: LoadBatch) -> tuple[int, int, int]:
            assert batch.storage_path is None
            return (1, 1, 1)

    args = _sample_args()
    args.dry_run = False
    args.allow_missing_r2 = True
    args.write_target = "staging"
    monkeypatch.setenv("DATABASE_URL_STAGING", "postgresql://staging.example/db")
    monkeypatch.setattr(cli, "PostgresLoader", _FakeLoader)
    monkeypatch.setattr(cli, "Normalizer", _FakeNormalizer)
    monkeypatch.setattr(cli, "KakaoResolver", _FakeResolver)

    result = await cli._run_crawler(args, agency, _FakeCrawler(agency.id), _fake_row_extractor)

    assert result == 0
    assert loader_urls == ["postgresql://staging.example/db"]
