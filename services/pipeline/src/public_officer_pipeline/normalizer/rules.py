from __future__ import annotations

import re
from datetime import date
from uuid import UUID

from public_officer_pipeline.legal.visibility import (
    APPOINTED_RANKS,
    ALLOWED_ELECTED_RANKS,
    allowed_elected_ranks_for_agency,
)
from public_officer_pipeline.models import Agency, NormalizedVisit, ParsedExpenseRow, PlaceRaw
from public_officer_pipeline.legal.visibility import sanitize_raw_excerpt

SEOUL_DISTRICT_HINT_RE = re.compile(r"(?P<district>[가-힣]+구)(?:청|의회)?")


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
        place_raw = parse_place_text(row.place_text)
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
    if elected:
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
    department_name = _masked_department(value, fallback_department, rank_label, elected_ranks)
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
) -> str:
    cleaned_department = fallback_department.strip() or "서울시본청"
    if rank_label in elected_ranks:
        return cleaned_department
    if "직원" in user_text or rank_label == "5급 이하":
        return cleaned_department if "외" in cleaned_department else f"{cleaned_department} 외"
    return cleaned_department


def _person_re_for_ranks(ranks: tuple[str, ...]) -> re.Pattern[str]:
    rank_pattern = "|".join(sorted(ranks, key=len, reverse=True))
    return re.compile(rf"([가-힣]{{2,4}})\s*({rank_pattern})")


def _elected_ranks_for_agency(agency: Agency | None) -> tuple[str, ...]:
    if agency is None:
        return ALLOWED_ELECTED_RANKS
    return allowed_elected_ranks_for_agency(agency)


def _normalize_place_name(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
