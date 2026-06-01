from datetime import datetime

import pytest

from public_officer_pipeline.agencies import agency_uuid
from public_officer_pipeline.legal.visibility import (
    LegalVisibilityError,
    allowed_elected_ranks_for_agency,
    sanitize_raw_excerpt,
    validate_normalized_visit,
    validate_seoul_normalized_visit,
)
from public_officer_pipeline.models import (
    Agency,
    JurisdictionType,
    NormalizedVisit,
    ParsedExpenseRow,
    PipelineConfigError,
)
from public_officer_pipeline.normalizer import Normalizer, deterministic_normalize_rows, mask_user_text
from public_officer_pipeline.normalizer.llm import _coerce_visit_payload


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


def test_zero_party_size_is_treated_as_unknown() -> None:
    result = mask_user_text("진관동 0명", fallback_department="진관동")

    assert result["party_size"] is None


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


def test_deterministic_normalizer_skips_placeholder_place_text() -> None:
    visits = deterministic_normalize_rows(
        agency_id=agency_uuid("성동구:office"),
        source_url="https://example.test/source.pdf",
        source_title="성동구청 업무추진비",
        source_published_at=None,
        source_hash_sha256="hash",
        rows=[
            ParsedExpenseRow(
                department_name="성동구청 총무과",
                used_at=datetime(2026, 2, 2, 12, 29),
                place_text="정보 없음",
                purpose="현안 업무 추진 직원 격려",
                amount=27400,
                user_text="총무과 직원(7명)",
                payment_method="카드결제",
                raw_excerpt="정보 없음",
            ),
            ParsedExpenseRow(
                department_name="성동구청 총무과",
                used_at=datetime(2026, 2, 3, 12, 29),
                place_text="반가안동국시",
                purpose="현안 업무 추진 직원 격려",
                amount=40000,
                user_text="총무과 직원(7명)",
                payment_method="카드결제",
                raw_excerpt="반가안동국시",
            ),
        ],
    )

    assert [visit.place_raw.name for visit in visits] == ["반가안동국시"]


def _visit(**overrides: object) -> NormalizedVisit:
    data = {
        "agency_id": agency_uuid("성동구:office"),
        "source_url": "https://example.test/source.pdf",
        "source_title": "서울시 업무추진비",
        "source_published_at": None,
        "source_hash_sha256": "hash",
        "visit_date": datetime(2026, 4, 1).date(),
        "amount": 10000,
        "department_name": "총무국",
        "rank_label": "시장",
        "representative": "홍길동",
        "place_raw": {"name": "샤브하우스", "address_hint": None},
        "raw_excerpt": "홍길동 국장",
        "confidence": 0.92,
    }
    data.update(overrides)
    return NormalizedVisit.model_validate(data)


def _agency(parent_region: str, jurisdiction_type: JurisdictionType = JurisdictionType.SPECIAL_CITY) -> Agency:
    return Agency(parent_region=parent_region, jurisdiction_type=jurisdiction_type)


def test_legal_visibility_allows_elected_representative_in_seoul() -> None:
    visit = _visit(rank_label="구의원", representative="박영희", raw_excerpt="의안 검토 간담회")

    validated = validate_seoul_normalized_visit(visit)

    assert validated.representative == "박영희"


def test_legal_visibility_masks_elected_rank_out_of_region() -> None:
    visit = _visit(rank_label="도지사", representative="홍길동", raw_excerpt="의안 검토 간담회")

    validated = validate_normalized_visit(visit, agency=_agency("서울특별시"))

    assert validated.representative is None


def test_legal_visibility_treats_zero_party_size_as_unknown() -> None:
    visit = _visit(party_size=0, raw_excerpt="간담회")

    validated = validate_normalized_visit(visit, agency=_agency("서울특별시"))

    assert validated.party_size is None


def test_legal_visibility_allows_gyeonggi_elected_ranks() -> None:
    agency = _agency("경기도", JurisdictionType.PROVINCE)

    assert allowed_elected_ranks_for_agency(agency) == ("도지사", "시장", "군수", "도의원", "시의원", "군의원")

    for rank in ("도지사", "군수", "도의원"):
        visit = _visit(rank_label=rank, representative="홍길동", agency_id=agency_uuid("gyeonggi:province:office"))
        validated = validate_normalized_visit(visit, agency=agency)
        assert validated.representative == "홍길동"


def test_legal_visibility_allows_incheon_elected_ranks() -> None:
    agency = _agency("인천광역시", JurisdictionType.METRO_CITY)

    for rank in ("시장", "군수", "구의원"):
        visit = _visit(rank_label=rank, representative="김철수", agency_id=agency_uuid("incheon:metro:office"))
        validated = validate_normalized_visit(visit, agency=agency)
        assert validated.representative == "김철수"


def test_legal_visibility_allows_non_capital_elected_ranks() -> None:
    daejeon = _agency("대전광역시", JurisdictionType.METRO_CITY)
    assert allowed_elected_ranks_for_agency(daejeon) == ("시장", "구청장", "군수", "시의원", "구의원", "군의원")
    visit = _visit(rank_label="시의원", representative="김철수", agency_id=agency_uuid("daejeon:regional:council"))
    assert validate_normalized_visit(visit, agency=daejeon).representative == "김철수"

    sejong = _agency("세종특별자치시", JurisdictionType.SPECIAL_SELF_GOVERNING_CITY)
    assert allowed_elected_ranks_for_agency(sejong) == ("시장", "시의원")
    visit = _visit(rank_label="구청장", representative="김철수", agency_id=agency_uuid("sejong:regional:office"))
    assert validate_normalized_visit(visit, agency=sejong).representative is None

    jeju = _agency("제주특별자치도", JurisdictionType.SPECIAL_SELF_GOVERNING_PROVINCE)
    assert allowed_elected_ranks_for_agency(jeju) == ("도지사", "도의원")
    visit = _visit(rank_label="도지사", representative="김철수", agency_id=agency_uuid("jeju:regional:office"))
    assert validate_normalized_visit(visit, agency=jeju).representative == "김철수"


def test_legal_visibility_masks_general_or_appointed_ranks_outside_elected_allowlist() -> None:
    visit = _visit(rank_label="국장", representative="박영희", raw_excerpt="점심 식사")
    validated = validate_normalized_visit(visit, agency=_agency("경기도", JurisdictionType.PROVINCE))

    assert validated.representative is None

    visit = _visit(rank_label="부지사", representative="이길동", raw_excerpt="오후 회의")
    validated = validate_normalized_visit(visit, agency=_agency("경기도", JurisdictionType.PROVINCE))

    assert validated.representative is None


def test_sanitize_raw_excerpt_masks_obvious_name_rank_pairs() -> None:
    assert sanitize_raw_excerpt("홍길동 국장") == "○○ 국장"
    assert sanitize_raw_excerpt("김철수 과장") == "○○ 과장"
    assert sanitize_raw_excerpt("이영희 동장") == "○○ 동장"
    assert sanitize_raw_excerpt("박영희구청장 외 2명") == "○○구청장 외 2명"


def test_department_name_with_name_rank_is_rejected() -> None:
    with pytest.raises(LegalVisibilityError):
        validate_normalized_visit(_visit(department_name="홍길동 국장"), agency=_agency("서울특별시"))


def test_department_name_with_eup_myeon_dong_head_name_is_rejected() -> None:
    with pytest.raises(LegalVisibilityError):
        validate_normalized_visit(_visit(department_name="이영희 동장"), agency=_agency("경기도"))


def test_department_name_with_embedded_name_rank_is_rejected() -> None:
    with pytest.raises(LegalVisibilityError):
        validate_normalized_visit(_visit(department_name="총무과 이영희 동장"), agency=_agency("경기도"))


@pytest.mark.asyncio
async def test_non_seoul_normalization_blocks_missing_agency_context() -> None:
    normalizer = Normalizer(allow_deterministic_fallback=True)
    with pytest.raises(PipelineConfigError, match="Non-Seoul agencies require explicit Agency context"):
        await normalizer.normalize_rows(
            agency_id=agency_uuid("gyeonggi:province:office"),
            source_url="https://example.test/source.pdf",
            source_title="test",
            source_published_at=None,
            source_hash_sha256="hash",
            rows=[
                ParsedExpenseRow(
                    department_name="의회",
                    used_at=datetime(2026, 5, 1, 12),
                    place_text="테스트 식당",
                    amount=10000,
                    user_text="도지사 홍길동",
                    raw_excerpt="회의 비용",
                )
            ],
        )


def test_llm_visit_payload_coercion_accepts_common_shape_drift() -> None:
    payload = _coerce_visit_payload(
        {
            "visit_date": "2026-04-24T12:32:00",
            "source_published_at": "2026-05-01T00:00:00",
            "amount": 10000,
            "place_raw": "지베",
            "raw_excerpt": "총무과 직원",
            "confidence": "0.91",
        }
    )

    assert payload["visit_date"] == "2026-04-24"
    assert payload["source_published_at"] == "2026-05-01"
    assert payload["place_raw"] == {"name": "지베", "address_hint": None}
    assert payload["confidence"] == 0.91


def test_llm_visit_payload_coercion_accepts_qualitative_confidence() -> None:
    payload = _coerce_visit_payload(
        {
            "visit_date": "2026-04-24",
            "amount": 10000,
            "place_raw": "지베",
            "raw_excerpt": "총무과 직원",
            "confidence": "high",
        }
    )

    assert payload["confidence"] == 0.9


def test_llm_visit_payload_coercion_defaults_null_confidence() -> None:
    payload = _coerce_visit_payload(
        {
            "visit_date": "2026-04-24",
            "amount": 10000,
            "place_raw": "지베",
            "raw_excerpt": "총무과 직원",
            "confidence": None,
        }
    )

    assert payload["confidence"] == 0.8
