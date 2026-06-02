from __future__ import annotations

import re
from datetime import date
from uuid import UUID

from public_officer_pipeline.legal.visibility import (
    APPOINTED_RANKS,
    ALLOWED_ELECTED_RANKS,
    allowed_elected_ranks_for_agency,
)
from public_officer_pipeline.entity.policy import is_valid_place_name
from public_officer_pipeline.models import Agency, NormalizedVisit, ParsedExpenseRow, PlaceRaw
from public_officer_pipeline.legal.visibility import sanitize_raw_excerpt

SEOUL_DISTRICT_HINT_RE = re.compile(r"(?P<district>[가-힣]+구)(?:청|의회)?")
NON_PLACE_EXPENSE_RE = re.compile(r"경조사|축의금|조의금|부의금|부조금|화환|격려금")
SUMMARY_PLACE_RE = re.compile(r"^\s*(?:합계|총계|\d+(?:\s*건)?|-)\s*$")
PURPOSE_ONLY_PLACE_RE = re.compile(
    r"간담회|정례회|대응|결혼\s*축하|축하금|임직원\s*소통|업무협의|정책협의|"
    r"주요정책추진|회의|행사|유관(?:\s*기관|\(관련\)\s*기관)"
)


def deterministic_normalize_rows(
    *,
    agency: Agency | None = None,
    agency_id: UUID,
    source_url: str,
    source_title: str,
    source_published_at: date | None,
    source_hash_sha256: str,
    rows: list[ParsedExpenseRow],
) -> list[NormalizedVisit]:
    visits: list[NormalizedVisit] = []
    for row in rows:
        if _is_non_place_expense(row):
            continue
        place_raw = parse_place_text(row.place_text)
        if not is_valid_place_name(place_raw.name):
            continue
        if not place_raw.address_hint:
            region_hint = _region_hint_from_department(row.department_name)
            if region_hint:
                place_raw = PlaceRaw(name=place_raw.name, address_hint=region_hint)
        mask = mask_user_text(
            row.user_text or "",
            fallback_department=row.department_name,
            agency=agency,
        )
        visits.append(
            NormalizedVisit(
                agency_id=agency_id,
                source_url=source_url,
                source_title=source_title,
                source_published_at=source_published_at,
                source_hash_sha256=source_hash_sha256,
                visit_date=row.used_at.date(),
                amount=row.amount,
                party_size=mask["party_size"],
                purpose=row.purpose,
                department_name=mask["department_name"],
                rank_label=mask["rank_label"],
                representative=mask["representative"],
                payment_method=row.payment_method,
                expense_category=row.expense_category,
                place_raw=place_raw,
                raw_excerpt=sanitize_raw_excerpt(row.raw_excerpt),
                confidence=0.82,
            )
        )
    return visits


def _is_non_place_expense(row: ParsedExpenseRow) -> bool:
    place = re.sub(r"\s+", "", row.place_text or "")
    purpose = re.sub(r"\s+", "", row.purpose or "")
    if place and purpose and place == purpose and PURPOSE_ONLY_PLACE_RE.search(row.place_text):
        return True
    joined = " ".join(
        value
        for value in (
            row.place_text,
            row.purpose or "",
            row.expense_category or "",
            row.raw_excerpt,
        )
        if value
    )
    if NON_PLACE_EXPENSE_RE.search(joined):
        return True
    return bool(SUMMARY_PLACE_RE.fullmatch(row.place_text))


def parse_place_text(place_text: str) -> PlaceRaw:
    value = re.sub(r"\s+", " ", place_text).strip()
    match = re.match(r"^(?P<name>.+?)\((?P<address>[^()]+)\)\s*$", value)
    if match:
        return PlaceRaw(name=_normalize_place_name(match.group("name")), address_hint=match.group("address").strip())
    return PlaceRaw(name=_normalize_place_name(value), address_hint=None)


def _region_hint_from_department(department_name: str) -> str | None:
    match = SEOUL_DISTRICT_HINT_RE.search(department_name)
    if not match:
        return None
    return f"서울 {match.group('district')}"


def mask_user_text(
    user_text: str,
    fallback_department: str,
    agency: Agency | None = None,
) -> dict[str, str | int | None]:
    value = re.sub(r"\s+", " ", user_text).strip()
    representative: str | None = None
    rank_label: str | None = None
    elected_ranks = _elected_ranks_for_agency(agency)
    elected_re = _person_re_for_ranks(elected_ranks)

    elected = elected_re.search(value)
    if elected and not _looks_like_institutional_elected_subject(elected.group(1), agency):
        representative = elected.group(1)
        rank_label = elected.group(2)
    else:
        for rank in elected_ranks:
            if rank in value:
                rank_label = rank
                break
        for rank in APPOINTED_RANKS:
            if rank_label:
                break
            if rank in value:
                rank_label = rank
                break
    if not rank_label:
        rank_label = "5급 이하"
    elif rank_label == "직원":
        rank_label = "5급 이하"

    party_size = _parse_party_size(value)
    department_name = _masked_department(value, fallback_department, rank_label, elected_ranks, agency)
    return {
        "party_size": party_size,
        "department_name": department_name,
        "rank_label": rank_label,
        "representative": representative,
    }


def _parse_party_size(value: str) -> int | None:
    if not value:
        return None
    for pattern, add_one in ((r"외\s*(\d+)\s*[명인]", True), (r"(\d+)\s*[명인]", False)):
        match = re.search(pattern, value)
        if match:
            count = int(match.group(1))
            party_size = count + 1 if add_one else count
            return party_size if party_size > 0 else None
    return None


def _masked_department(
    user_text: str,
    fallback_department: str,
    rank_label: str,
    elected_ranks: tuple[str, ...],
    agency: Agency | None = None,
) -> str:
    cleaned_department = fallback_department.strip() or "서울시본청"
    if rank_label in elected_ranks:
        return _strip_institutional_elected_rank_department(cleaned_department, rank_label, agency)
    if "직원" in user_text or rank_label == "5급 이하":
        return cleaned_department if "외" in cleaned_department else f"{cleaned_department} 외"
    return cleaned_department


def _strip_institutional_elected_rank_department(
    department: str,
    rank_label: str,
    agency: Agency | None,
) -> str:
    match = re.match(rf"^(?P<prefix>.+)\s+{re.escape(rank_label)}$", department)
    if not match:
        return department
    prefix = match.group("prefix").strip()
    if _looks_like_institutional_elected_subject(prefix, agency):
        return prefix
    return department


def _looks_like_institutional_elected_subject(value: str, agency: Agency | None) -> bool:
    compact = re.sub(r"\s+", "", value)
    if compact.endswith(("시청", "군청", "구청", "도청", "의회")):
        return True
    if agency is None:
        return False
    candidates = {
        agency.name,
        agency.short_name,
        agency.parent_region,
        agency.sub_region or "",
    }
    normalized_candidates = {re.sub(r"\s+", "", candidate) for candidate in candidates if candidate}
    return compact in normalized_candidates


def _person_re_for_ranks(ranks: tuple[str, ...]) -> re.Pattern[str]:
    rank_pattern = "|".join(sorted(ranks, key=len, reverse=True))
    return re.compile(rf"([가-힣]{{2,4}})\s*({rank_pattern})")


def _elected_ranks_for_agency(agency: Agency | None) -> tuple[str, ...]:
    if agency is None:
        return ALLOWED_ELECTED_RANKS
    return allowed_elected_ranks_for_agency(agency)


def _normalize_place_name(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
