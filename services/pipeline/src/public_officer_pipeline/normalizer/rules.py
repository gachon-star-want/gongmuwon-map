from __future__ import annotations

import re
from datetime import date
from uuid import UUID

from public_officer_pipeline.models import NormalizedVisit, ParsedExpenseRow, PlaceRaw


ELECTED_RANKS = ("시장", "구청장", "시의원", "구의원")
APPOINTED_RANKS = ("부시장", "실장", "국장", "본부장", "과장", "팀장", "담당관", "전문위원")
PERSON_RE = re.compile(r"([가-힣]{2,4})\s*(시장|구청장|시의원|구의원)")


def deterministic_normalize_rows(
    *,
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
        mask = mask_user_text(row.user_text or "", fallback_department=row.department_name)
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
                raw_excerpt=row.raw_excerpt,
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


def mask_user_text(user_text: str, fallback_department: str) -> dict[str, str | int | None]:
    value = re.sub(r"\s+", " ", user_text).strip()
    representative: str | None = None
    rank_label: str | None = None

    elected = PERSON_RE.search(value)
    if elected:
        representative = elected.group(1)
        rank_label = elected.group(2)
    else:
        for rank in APPOINTED_RANKS:
            if rank in value:
                rank_label = rank
                break
    if not rank_label:
        rank_label = "5급 이하"

    party_size = _parse_party_size(value)
    department_name = _masked_department(value, fallback_department, rank_label)
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
            return count + 1 if add_one else count
    return None


def _masked_department(user_text: str, fallback_department: str, rank_label: str) -> str:
    cleaned_department = fallback_department.strip() or "서울시본청"
    if rank_label in ELECTED_RANKS:
        return cleaned_department
    if "직원" in user_text or rank_label == "5급 이하":
        return cleaned_department if "외" in cleaned_department else f"{cleaned_department} 외"
    return cleaned_department


def _normalize_place_name(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
