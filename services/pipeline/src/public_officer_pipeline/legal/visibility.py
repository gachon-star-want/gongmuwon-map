from __future__ import annotations

import re

from public_officer_pipeline.models import Agency, NormalizedVisit

ALLOWED_ELECTED_RANKS = ("시장", "구청장", "시의원", "구의원")
METRO_CITY_ELECTED_RANKS = ("시장", "구청장", "군수", "시의원", "구의원", "군의원")
PROVINCE_ELECTED_RANKS = ("도지사", "시장", "군수", "도의원", "시의원", "군의원")
ELECTED_RANKS_BY_PARENT_REGION = {
    "서울특별시": ("시장", "구청장", "시의원", "구의원"),
    "부산광역시": METRO_CITY_ELECTED_RANKS,
    "대구광역시": METRO_CITY_ELECTED_RANKS,
    "인천광역시": METRO_CITY_ELECTED_RANKS,
    "광주광역시": METRO_CITY_ELECTED_RANKS,
    "대전광역시": METRO_CITY_ELECTED_RANKS,
    "울산광역시": METRO_CITY_ELECTED_RANKS,
    "세종특별자치시": ("시장", "시의원"),
    "경기도": PROVINCE_ELECTED_RANKS,
    "강원특별자치도": PROVINCE_ELECTED_RANKS,
    "충청북도": PROVINCE_ELECTED_RANKS,
    "충청남도": PROVINCE_ELECTED_RANKS,
    "전북특별자치도": PROVINCE_ELECTED_RANKS,
    "전라남도": PROVINCE_ELECTED_RANKS,
    "경상북도": PROVINCE_ELECTED_RANKS,
    "경상남도": PROVINCE_ELECTED_RANKS,
    "제주특별자치도": ("도지사", "도의원"),
}
APPOINTED_RANKS = (
    "부시장",
    "부지사",
    "부군수",
    "부구청장",
    "실장",
    "국장",
    "본부장",
    "과장",
    "팀장",
    "담당관",
    "전문위원",
    "읍장",
    "면장",
    "동장",
    "주무관",
    "직원",
    "행정관",
    "연구사",
    "지도사",
)
ELECTED_RANKS = ALLOWED_ELECTED_RANKS

_ALL_RANKS = tuple(
    dict.fromkeys(
        APPOINTED_RANKS
        + tuple({rank for ranks in ELECTED_RANKS_BY_PARENT_REGION.values() for rank in ranks})
    )
)
_RANK_PATTERN = "|".join(sorted(_ALL_RANKS, key=len, reverse=True))
_PERSON_NAME_WITH_RANK_RE = re.compile(
    rf"(?<![가-힣a-zA-Z0-9_])(?P<name>[가-힣]{{2,4}})(?P<sep>\s*)(?P<rank>{_RANK_PATTERN})(?![가-힣])"
)


class LegalVisibilityError(ValueError):
    pass


def allowed_elected_ranks_for_agency(agency: Agency) -> tuple[str, ...]:
    if agency.expansion_phase.value in {"p2", "p3", "p4"}:
        return ()
    ranks = ELECTED_RANKS_BY_PARENT_REGION.get(agency.parent_region)
    if ranks is None:
        raise LegalVisibilityError(
            f"Unsupported parent_region for masking policy: {agency.parent_region}; "
            "add a nationwide elected-rank mapping before loading"
        )
    return ranks


def sanitize_raw_excerpt(value: str | None) -> str:
    return _mask_name_rank_pairs(value or "")


def validate_normalized_visit(visit: NormalizedVisit, *, agency: Agency) -> NormalizedVisit:
    allowed_elected_ranks = allowed_elected_ranks_for_agency(agency)

    rank_label = visit.rank_label
    representative = visit.representative
    if representative is not None and rank_label not in allowed_elected_ranks:
        representative = None

    department_name = _validate_department_name(visit.department_name)
    purpose = _mask_name_rank_pairs(visit.purpose or "") or None
    party_size = visit.party_size if visit.party_size and visit.party_size > 0 else None

    raw_excerpt = sanitize_raw_excerpt(visit.raw_excerpt)

    return visit.model_copy(
        update={
            "department_name": department_name,
            "party_size": party_size,
            "purpose": purpose,
            "representative": representative,
            "raw_excerpt": raw_excerpt,
        }
    )


def validate_normalized_visits(visits: list[NormalizedVisit], *, agency: Agency) -> list[NormalizedVisit]:
    return [validate_normalized_visit(visit, agency=agency) for visit in visits]


def _mask_name_rank_pairs(value: str) -> str:
    return _PERSON_NAME_WITH_RANK_RE.sub(_name_rank_replacement, value).strip()


def _name_rank_replacement(match: re.Match[str]) -> str:
    return f"○○{match.group('sep')}{match.group('rank')}"


def _validate_department_name(value: str | None) -> str | None:
    if value is None:
        return value
    for match in _PERSON_NAME_WITH_RANK_RE.finditer(value):
        if _is_department_unit_rank_false_positive(match):
            continue
        raise LegalVisibilityError(f"department_name contains unmasked personal identity: {value}")
    return value


def _is_department_unit_rank_false_positive(match: re.Match[str]) -> bool:
    rank = match.group("rank")
    if rank not in {"담당관", "전문위원"}:
        return False
    if match.group("sep"):
        return False
    name = match.group("name")
    # Korean department units such as "의사입법담당관" or "감사담당관"
    # often look like a name directly followed by an appointed rank. Keep
    # three-syllable prefixes rejected because they are the common personal-name
    # shape in strings like "홍길동담당관".
    return len(name) != 3
