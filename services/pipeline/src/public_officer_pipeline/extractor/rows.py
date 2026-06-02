from __future__ import annotations

import re
from datetime import date, datetime, time
from dateutil import parser as date_parser
from pydantic import BaseModel, Field

from public_officer_pipeline.legal.visibility import sanitize_raw_excerpt
from public_officer_pipeline.models import ParsedExpenseRow


_SHORT_YEAR_DATE_RE = re.compile(
    r"^\s*(?P<year>\d{2})\s*[./-]\s*(?P<month>\d{1,2})\s*[./-]\s*(?P<day>\d{1,2})(?P<rest>.*)$"
)
_FULL_YEAR_DATE_RE = re.compile(
    r"^\s*(?P<year>20\d{2})\s*[./-]\s*(?P<month>\d{1,2})\s*[./-]\s*(?P<day>\d{1,2})(?P<rest>.*)$"
)
_VALID_TIME_RE = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?\b")
_TIME_LIKE_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
_BARE_DAY_RE = re.compile(r"^\d{1,2}$")


class RawExpenseFields(BaseModel):
    department_name: str | None = None
    date_text: str | None = None
    time_text: str | None = None
    used_at: datetime | None = None
    place_name: str | None = None
    address: str | None = None
    address_hint: str | None = None
    place_text: str | None = None
    purpose: str | None = None
    amount: str | int | None = None
    amount_is_thousands: bool = False
    party_size: str | int | None = None
    user_text: str | None = None
    payment_method: str | None = None
    expense_category: str | None = None
    raw_values: list[str] = Field(default_factory=list)


def build_expense_row(
    fields: RawExpenseFields, *, fallback_department: str, address_separator: str = "("
) -> ParsedExpenseRow | None:
    return _build_expense_row(
        fields,
        fallback_department=fallback_department,
        address_separator=address_separator,
    )


def _build_expense_row(
    fields: RawExpenseFields,
    *,
    fallback_department: str,
    address_separator: str = "(",
) -> ParsedExpenseRow | None:
    department_name = _clean(fields.department_name or fallback_department) or "서울시본청"
    used_at = fields.used_at
    if used_at is None:
        used_at = parse_used_at(fields.date_text, fields.time_text)
    if used_at is None:
        return None

    amount = parse_amount(fields.amount)
    if amount is None:
        return None
    if fields.amount_is_thousands:
        amount *= 1000
    if amount <= 0:
        return None

    place_text = format_place_text(
        name=fields.place_name,
        address=fields.address,
        address_hint=fields.address_hint,
        place_text=fields.place_text,
        address_separator=address_separator,
    )
    if not place_text:
        return None

    user_text = _clean(fields.user_text)
    party_size = parse_party_size(fields.party_size)
    if user_text and party_size:
        user_text = f"{user_text} {party_size}명"
    elif not user_text and party_size and not fields.place_name:
        # Keep old behavior for callers that intentionally set no user text by design.
        user_text = None

    raw_excerpt = " | ".join(value for value in (_clean(value) for value in fields.raw_values) if value)
    if raw_excerpt:
        raw_excerpt = sanitize_raw_excerpt(raw_excerpt)

    return ParsedExpenseRow(
        department_name=department_name,
        used_at=used_at,
        place_text=place_text,
        purpose=_clean(fields.purpose),
        amount=amount,
        user_text=user_text,
        payment_method=_clean(fields.payment_method),
        expense_category=_clean(fields.expense_category),
        raw_excerpt=raw_excerpt,
    )


def parse_amount(value: str | int | None) -> int | None:
    if value is None:
        return None
    numeric_text = re.sub(r"[^\d]", "", str(value))
    if not numeric_text:
        return None
    return int(numeric_text)


def parse_party_size(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    numeric = re.sub(r"[^\d]", "", str(value))
    if not numeric:
        return None
    return int(numeric) if int(numeric) > 0 else None


def parse_used_at(date_text: str | None, time_text: str | None) -> datetime | None:
    if date_text is None:
        return None
    if isinstance(date_text, str):
        date_value = _clean(date_text)
    else:
        date_value = str(date_text)
    if not date_value:
        return None
    if _BARE_DAY_RE.fullmatch(date_value):
        return None

    numeric_date = _parse_numeric_datetime(date_value, time_text)
    if numeric_date:
        return numeric_date.replace(tzinfo=None)

    combined_time = _extract_time_text(time_text)
    combined = f"{date_value} {combined_time}" if combined_time else date_value
    try:
        parsed = date_parser.parse(combined, fuzzy=True)
    except (TypeError, ValueError):
        return None
    return parsed.replace(tzinfo=None)


def format_place_text(
    name: str | None,
    address: str | None,
    address_hint: str | None = None,
    place_text: str | None = None,
    address_separator: str = "(",
) -> str | None:
    explicit_place = _clean(place_text)
    normalized_name = _clean(name)
    normalized_address = _clean(address) or _clean(address_hint)

    if explicit_place and (("(" in explicit_place or "（" in explicit_place) or not normalized_name):
        return explicit_place

    if not normalized_name:
        return None

    if normalized_address:
        return f"{normalized_name}{address_separator}{normalized_address})"
    return normalized_name


def _extract_time_text(time_text: str | None) -> str | None:
    if not time_text:
        return None
    compact = _clean(time_text)
    if not compact:
        return None
    match = _VALID_TIME_RE.search(compact)
    if match:
        return match.group(0)
    return compact


def _parse_numeric_datetime(date_value: str, time_text: str | None) -> datetime | None:
    match = _FULL_YEAR_DATE_RE.match(date_value)
    short_year = False
    if not match:
        match = _SHORT_YEAR_DATE_RE.match(date_value)
        short_year = True
    if not match:
        return None

    try:
        year = int(match.group("year"))
        month = int(match.group("month"))
        day = int(match.group("day"))
        if short_year:
            year = 2000 + year if year < 70 else 1900 + year
        parsed_date = date(year, month, day)
    except ValueError:
        return None

    parse_time = time_text or None
    rest = match.group("rest")
    if not parse_time:
        parse_time = _extract_time_from_text(rest)
        if parse_time is None and _TIME_LIKE_RE.search(rest or ""):
            return None
    if parse_time is None:
        return datetime.combine(parsed_date, time.min)

    try:
        parsed = date_parser.parse(f"{parsed_date.isoformat()} {parse_time}", fuzzy=True)
    except (TypeError, ValueError):
        return None
    return parsed.replace(tzinfo=None)


def _extract_time_from_text(value: str | None) -> str | None:
    if not value:
        return None
    match = _VALID_TIME_RE.search(value)
    if match:
        return match.group(0)
    try:
        parsed = date_parser.parse(value, fuzzy=True)
        return parsed.time().isoformat(timespec="seconds")
    except (TypeError, ValueError):
        return None


def _clean(value: str | None) -> str | None:
    cleaned = re.sub(r"\s+", " ", value or "").strip()
    return cleaned or None
