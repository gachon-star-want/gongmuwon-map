from datetime import datetime

from public_officer_pipeline.models import ParsedExpenseRow
from public_officer_pipeline.normalizer import deterministic_normalize_rows, mask_user_text
from public_officer_pipeline.agencies import agency_uuid


def test_elected_official_can_keep_representative() -> None:
    result = mask_user_text("홍길동 시장 외 5명", fallback_department="시장실")

    assert result["representative"] == "홍길동"
    assert result["rank_label"] == "시장"
    assert result["party_size"] == 6


def test_appointed_official_name_is_not_kept() -> None:
    result = mask_user_text("박철수 국장(총무국) 외 2명", fallback_department="총무국")

    assert result["representative"] is None
    assert result["rank_label"] == "국장"
    assert result["party_size"] == 3


def test_staff_group_is_department_only() -> None:
    result = mask_user_text("총무과 직원 7명", fallback_department="총무과")

    assert result["representative"] is None
    assert result["rank_label"] == "5급 이하"
    assert result["department_name"] == "총무과 외"


def test_elected_rank_without_name_keeps_rank_only() -> None:
    result = mask_user_text("구의원 12명", fallback_department="구의회사무국")

    assert result["representative"] is None
    assert result["rank_label"] == "구의원"
    assert result["party_size"] == 12


def test_deterministic_normalizer_adds_seoul_district_hint_for_gu_department() -> None:
    visits = deterministic_normalize_rows(
        agency_id=agency_uuid("성동구:office"),
        source_url="https://example.test/source.pdf",
        source_title="성동구청 업무추진비",
        source_published_at=None,
        source_hash_sha256="hash",
        rows=[
            ParsedExpenseRow(
                department_name="성동구청 교통지도과",
                used_at=datetime(2026, 2, 2, 12, 29),
                place_text="나눔봉제 협동조합",
                purpose="현안 업무 추진 직원 격려",
                amount=27400,
                user_text="교통지도과 직원(7명)",
                payment_method="카드결제",
                raw_excerpt="",
            )
        ],
    )

    assert visits[0].place_raw.name == "나눔봉제 협동조합"
    assert visits[0].place_raw.address_hint == "서울 성동구"
