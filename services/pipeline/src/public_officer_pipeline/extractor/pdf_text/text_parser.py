from __future__ import annotations

import re

from dateutil import parser as date_parser

from public_officer_pipeline.extractor.rows import RawExpenseFields, build_expense_row
from public_officer_pipeline.models import ParsedExpenseRow


PDF_TEXT_ROW_RE = re.compile(
    r"^\s*\d+\s+"
    r"(?:(?P<user>[^0-9\n]{1,30}?)\s+)?"
    r"(?P<date>20\d{2}[.-]\d{1,2}[.-]\d{1,2}\.?)\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s+"
    r"(?P<body>.+?)\s*$"
)
PDF_TEXT_AMOUNT_RE = re.compile(
    r"\s(?P<amount>\d{1,3}(?:,\d{3})+|\d+)\s*"
    r"(?P<party_size>\d+)?\s*"
    r"(?P<payment_method>신용카드|카드|현금|제로페이|계좌이체)?\s*$"
)
PDF_TEXT_PURPOSE_FIRST_ROW_RE = re.compile(
    r"^\s*\d+\s+"
    r"(?P<date>20\d{2}[.-]\d{1,2}[.-]\d{1,2}\.?)\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s+"
    r"(?P<purpose>.+?)\s{2,}"
    r"(?P<amount>\d{1,3}(?:,\d{3})+|\d+)\s+"
    r"(?P<payment_method>신용카드|카드|현금|제로페이|계좌이체)\s+"
    r"(?P<place_text>.+?)\s{2,}"
    r"(?P<party_size>\d+|-)\s*$"
)
PDF_TEXT_USER_ADDRESS_ROW_RE = re.compile(
    r"^\s*\d+\s+"
    r"(?P<user>.+?)\s+"
    r"(?P<date>20\d{2}[.-]\d{1,2}[.-]\d{1,2}\.?)\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s+"
    r"(?P<body>.+?)\s+"
    r"(?P<party_size>\d+|-)\s+"
    r"(?P<amount>\d{1,3}(?:,\d{3})+|\d+)\s+"
    r"(?P<payment_method>신용카드|카드|현금|제로페이|계좌이체)\s+"
    r"(?P<expense_category>\S+)\s*$"
)
PDF_TEXT_PLACE_ADDRESS_PURPOSE_RE = re.compile(
    r"(?P<place>.+?)\s{2,}"
    r"(?P<address>서울(?:특별시|시)?\s+.+?)\s{2,}"
    r"(?P<purpose>.+)$"
)
PDF_TEXT_USER_NO_ADDRESS_ROW_RE = re.compile(
    r"^\s*(?:\d+\s+)?"
    r"(?P<user>.+?)\s+"
    r"(?P<date>20\d{2}[.]\s*\d{1,2}[.]\s*\d{1,2}[.]?)\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s+"
    r"(?P<body>.+?)\s+"
    r"(?P<party_size>\d+\s*명|-)\s+"
    r"(?P<amount>\d{1,3}(?:,\d{3})+|\d+)\s+"
    r"(?P<payment_method>신용카드|카드|현금|제로페이|계좌이체)\s+"
    r"(?P<expense_category>\S+)\s*$"
)
PDF_TEXT_USER_AMOUNT_PURPOSE_ROW_RE = re.compile(
    r"^\s*\d+\s+"
    r"(?P<user>.+?)\s+"
    r"(?P<date>20\d{2}[.-]\d{1,2}[.-]\d{1,2}[.]?)\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s+"
    r"(?P<place>.+?)\s+"
    r"(?P<amount>\d{1,3}(?:,\d{3})+|\d+)\s+"
    r"(?P<purpose>.+?)\s+"
    r"(?:(?P<party_size>\d+|-)\s+)?"
    r"(?P<payment_method>신용카드|카드|현금|제로페이|계좌이체)\s+"
    r"(?P<expense_category>\S+)\s*$"
)
PDF_TEXT_DATE_USER_AMOUNT_PLACE_ROW_RE = re.compile(
    r"^\s*\d+\s+"
    r"(?P<date>20\d{2}[.-]\d{1,2}[.-]\d{1,2}[.]?)\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s+"
    r"(?P<user>.+?)\s+"
    r"(?P<amount>\d{1,3}(?:,\d{3})+|\d+)\s+"
    r"(?P<body>.+?)\s+"
    r"(?P<party_size>\d+|-)\s+"
    r"(?P<payment_method>신용카드|카드|현금|제로페이|계좌이체)\s+"
    r"(?P<expense_category>\S+)\s*$"
)
PDF_TEXT_USER_PLACE_PURPOSE_AMOUNT_ROW_RE = re.compile(
    r"^\s*(?P<user>.+?)\s+"
    r"(?P<date>20\d{2}[.-]\d{1,2}[.-]\d{1,2}[.]?)\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s+"
    r"(?P<body>.+?)\s+"
    r"(?P<amount>\d{1,3}(?:,\d{3})+|\d+)\s+"
    r"(?P<party_size>\d+|-)\s+"
    r"(?P<payment_method>신용카드|카드|현금|제로페이|계좌이체)\s*$"
)
PDF_TEXT_PURPOSE_PLACE_AMOUNT_ROW_RE = re.compile(
    r"^\s*\d+\s+"
    r"(?P<date>20\d{2}[.-]\d{1,2}[.-]\d{1,2}[.]?)\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s+"
    r"(?P<body>.+?)\s+"
    r"(?P<party_size>\d+|-)\s+"
    r"(?P<amount>\d{1,3}(?:,\d{3})+|\d+)\s+"
    r"(?P<payment_method>신용카드|카드|현금|제로페이|계좌이체)\s*$"
)
PDF_TEXT_REGION_AMOUNT_PLACE_PURPOSE_ROW_RE = re.compile(
    r"^\s*(?P<region>서울시\s+\S+)\s+"
    r"(?P<date>20\d{2}[.-]\d{1,2}[.-]\d{1,2}[.]?)\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s+"
    r"(?P<amount>\d{1,3}(?:,\d{3})+|\d+)\s+"
    r"(?P<body>.+?)\s+"
    r"(?P<party_size>\d+|-)\s+"
    r"(?P<payment_method>신용카드|카드|현금|제로페이|계좌이체)\s+"
    r"(?P<user>.+?)\s*$"
)
PDF_TEXT_OPTIONAL_USER_PLACE_PURPOSE_AMOUNT_ROW_RE = re.compile(
    r"^\s*\d+\s+"
    r"(?:(?P<user>.+?)\s+)?"
    r"(?P<date>20\d{2}[.]\d{1,2}[.]\d{1,2}[.]?)\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s+"
    r"(?P<body>.+?)\s+"
    r"(?P<party_size>\d+|-)\s+"
    r"(?P<amount>\d{1,3}(?:,\d{3})+|\d+)\s+"
    r"(?P<payment_method>신용카드|카드|현금|제로페이|계좌이체)\s+"
    r"(?P<expense_category>\S+)\s*$"
)
PDF_TEXT_USER_AMOUNT_PLACE_ADDRESS_PURPOSE_ROW_RE = re.compile(
    r"^\s*\d+\s+"
    r"(?P<user>.+?)\s+"
    r"(?P<date>20\d{2}[.]\d{1,2}[.]\d{1,2}[.]?)\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s+"
    r"(?P<amount>\d{1,3}(?:,\d{3})+|\d+)\s+"
    r"(?P<body>.+?)\s+"
    r"(?P<target>(?:의원|직원|관계자|참석자|대상자)\s*등)\s+"
    r"(?P<party_size>\d+\s*명|-)\s+"
    r"(?P<payment_method>신용카드|카드|현금|제로페이|계좌이체)\s*$"
)
PDF_TEXT_SEGMENTED_OFFICE_USER_DATE_RE = re.compile(
    r"^(?P<user>.+?)\s+"
    r"(?P<date>20\d{6}|20\d{2}[.-]\d{1,2}[.-]\d{1,2}[.]?)\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)"
    r"(?:\s+(?P<tail>.+))?$"
)
PDF_TEXT_SEGMENTED_OFFICE_PAYMENT_RE = re.compile(
    r"(?P<payment_method>신용카드|카드|현금|제로페이|계좌이체)"
    r"(?:\s+(?P<expense_category>\S+))?"
)
PDF_TEXT_LAYOUT_DATE_RE = re.compile(r"20\d{2}[.]\s*\d{1,2}[.]\s*\d{1,2}[.]?")
PDF_TEXT_LAYOUT_DATE_OR_DASH_RE = re.compile(r"20\d{2}[.-]\s*\d{1,2}[.-]\s*\d{1,2}[.]?")
PDF_TEXT_LAYOUT_TIME_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
PDF_TEXT_LAYOUT_ROW_NUMBER_RE = re.compile(r"^\s*\d{1,3}\s+")
PDF_TEXT_LAYOUT_AMOUNT_RE = re.compile(r"\d{1,3}(?:,\d{3})+")
PDF_TEXT_LAYOUT_PAYMENT_RE = re.compile(r"카드결제|신용카드|카드|현금|제로페이|계좌이체")
PDF_TEXT_PURPOSE_STARTERS = (
    "의정활동",
    "직무수행",
    "의장 직무",
    "부의장 직무",
    "의회운영위원장",
    "기획행정위원장",
    "복지건설위원장",
    "의회사무국",
    "의회 현안",
    "의회 현한",
    "의정현안",
    "지역 현안",
    "지역현안",
    "의장 수행",
    "의장실",
    "의정활동",
    "생일",
    "주말",
    "노동절",
    "기획행정위원회",
    "복지건설위원회",
    "입법지원",
    "언론사",
    "2026년",
    "2026",
    "2025년",
    "2025회계연도",
    "2025",
    "소관",
    "의회사무국",
    "현안업무",
    "힐링",
    "지역 현안사항",
    "의회 현안사항",
    "원활한 의정활동",
    "영등포구의회",
    "설 명절",
    "의원 역량강화",
    "의정활동 홍보지원",
    "정월대보름",
)
PDF_TEXT_PURPOSE_STARTER_PATTERNS = (
    re.compile(r"제\d+회"),
)


def _build_pdf_row(
    payload: dict[str, str | int | None],
    *,
    fallback_department: str,
    raw_values: list[str] | None = None,
) -> ParsedExpenseRow | None:
    used_at_value = payload.get("used_at")
    cleaned_raw_values = [str(value) for value in (raw_values or []) if value is not None]
    return build_expense_row(
        RawExpenseFields(
            department_name=str(payload.get("department_name") or fallback_department),
            used_at=None,
            date_text=str(used_at_value) if used_at_value is not None else None,
            place_name=payload.get("place_name"),
            address=payload.get("address"),
            address_hint=payload.get("address_hint"),
            place_text=payload.get("place_text"),
            purpose=payload.get("purpose"),
            amount=payload.get("amount"),
            party_size=payload.get("party_size"),
            user_text=payload.get("user_text"),
            payment_method=payload.get("payment_method"),
            expense_category=payload.get("expense_category"),
            raw_values=cleaned_raw_values,
        ),
        fallback_department=fallback_department,
    )


def rows_from_pdf_text(text: str, *, fallback_department: str) -> list[ParsedExpenseRow]:
    from .grammars import build_default_grammars
    from .parser import parse_pdf_text_with_diagnostics

    line_grammars, whole_text_grammars = build_default_grammars()
    result = parse_pdf_text_with_diagnostics(
        text,
        fallback_department=fallback_department,
        line_grammars=line_grammars,
        whole_text_grammars=whole_text_grammars,
    )
    return result.rows


def _parse_pdf_text_line(line: str, *, fallback_department: str) -> ParsedExpenseRow | None:
    user_address = _parse_pdf_text_user_address_line(line, fallback_department=fallback_department)
    if user_address:
        return user_address
    date_user_amount_place = _parse_pdf_text_date_user_amount_place_line(
        line,
        fallback_department=fallback_department,
    )
    if date_user_amount_place:
        return date_user_amount_place
    purpose_place_amount = _parse_pdf_text_purpose_place_amount_line(
        line,
        fallback_department=fallback_department,
    )
    if purpose_place_amount:
        return purpose_place_amount
    region_amount_place_purpose = _parse_pdf_text_region_amount_place_purpose_line(
        line,
        fallback_department=fallback_department,
    )
    if region_amount_place_purpose:
        return region_amount_place_purpose
    optional_user_place_purpose_amount = _parse_pdf_text_optional_user_place_purpose_amount_line(
        line,
        fallback_department=fallback_department,
    )
    if optional_user_place_purpose_amount:
        return optional_user_place_purpose_amount
    user_amount_place_address_purpose = _parse_pdf_text_user_amount_place_address_purpose_line(
        line,
        fallback_department=fallback_department,
    )
    if user_amount_place_address_purpose:
        return user_amount_place_address_purpose
    user_place_purpose_amount = _parse_pdf_text_user_place_purpose_amount_line(
        line,
        fallback_department=fallback_department,
    )
    if user_place_purpose_amount:
        return user_place_purpose_amount
    user_amount_purpose = _parse_pdf_text_user_amount_purpose_line(line, fallback_department=fallback_department)
    if user_amount_purpose:
        return user_amount_purpose
    user_no_address = _parse_pdf_text_user_no_address_line(line, fallback_department=fallback_department)
    if user_no_address:
        return user_no_address
    purpose_first = _parse_pdf_text_purpose_first_line(line, fallback_department=fallback_department)
    if purpose_first:
        return purpose_first
    return _parse_pdf_text_generic_row(line, fallback_department=fallback_department)


def _parse_pdf_text_generic_row(line: str, *, fallback_department: str) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_ROW_RE.match(line)
    if not row_match:
        return None
    body = row_match.group("body")
    amount_match = PDF_TEXT_AMOUNT_RE.search(body)
    if not amount_match:
        return None
    place_and_purpose = body[: amount_match.start()].rstrip()
    parts = re.split(r"\s{2,}", place_and_purpose, maxsplit=1)
    if len(parts) != 2:
        return None
    place_text, purpose = (part.strip() for part in parts)
    if not place_text or not purpose:
        return None
    party_size = amount_match.group("party_size")
    return _build_pdf_row(
        {
            "used_at": f"{row_match.group('date')} {row_match.group('time')}",
            "place_text": place_text,
            "purpose": purpose,
            "amount": amount_match.group("amount"),
            "party_size": party_size,
            "user_text": row_match.group("user"),
            "payment_method": amount_match.group("payment_method"),
        },
        fallback_department=fallback_department,
        raw_values=[
            row_match.group("date"),
            row_match.group("time"),
            place_text,
            purpose,
            amount_match.group("amount"),
            party_size,
            amount_match.group("payment_method"),
        ],
    )


def _parse_pdf_text_user_address_line(line: str, *, fallback_department: str) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_USER_ADDRESS_ROW_RE.match(line)
    if not row_match:
        return None
    body_match = PDF_TEXT_PLACE_ADDRESS_PURPOSE_RE.match(row_match.group("body").strip())
    if not body_match:
        return None
    party_size = row_match.group("party_size")
    place = body_match.group("place").strip()
    address = body_match.group("address").strip()
    purpose = body_match.group("purpose").strip()
    if party_size == "-":
        party_size = None
    return _build_pdf_row(
        {
            "used_at": f"{row_match.group('date')} {row_match.group('time')}",
            "place_name": place,
            "address": address,
            "purpose": purpose,
            "amount": row_match.group("amount"),
            "party_size": party_size,
            "user_text": "구의원",
            "payment_method": row_match.group("payment_method"),
            "expense_category": row_match.group("expense_category"),
        },
        fallback_department=fallback_department,
        raw_values=[
            row_match.group("user"),
            row_match.group("date"),
            row_match.group("time"),
            place,
            address,
            purpose,
            party_size,
            row_match.group("amount"),
            row_match.group("payment_method"),
            row_match.group("expense_category"),
        ],
    )


def _parse_pdf_text_date_user_amount_place_line(line: str, *, fallback_department: str) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_DATE_USER_AMOUNT_PLACE_ROW_RE.match(line)
    if not row_match:
        return None
    place, purpose = _split_place_and_purpose(row_match.group("body").strip(), row_match.group("user").strip())
    if not place or not purpose:
        return None
    party_size = row_match.group("party_size")
    if party_size == "-":
        party_size = None
    return _build_pdf_row(
        {
            "used_at": f"{row_match.group('date')} {row_match.group('time')}",
            "place_name": place,
            "purpose": purpose,
            "amount": row_match.group("amount"),
            "party_size": party_size,
            "user_text": row_match.group("user").strip(),
            "payment_method": row_match.group("payment_method"),
            "expense_category": row_match.group("expense_category"),
        },
        fallback_department=fallback_department,
        raw_values=[
            row_match.group("date"),
            row_match.group("time"),
            row_match.group("user"),
            row_match.group("amount"),
            place,
            purpose,
            party_size,
            row_match.group("payment_method"),
            row_match.group("expense_category"),
        ],
    )


def _parse_pdf_text_purpose_place_amount_line(line: str, *, fallback_department: str) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_PURPOSE_PLACE_AMOUNT_ROW_RE.match(line)
    if not row_match:
        return None
    purpose, place = _split_purpose_and_place(row_match.group("body").strip())
    if not place or not purpose:
        return None
    party_size = row_match.group("party_size")
    if party_size == "-":
        party_size = None
    return _build_pdf_row(
        {
            "used_at": f"{row_match.group('date')} {row_match.group('time')}",
            "place_name": place,
            "purpose": purpose,
            "amount": row_match.group("amount"),
            "party_size": party_size,
            "user_text": fallback_department,
            "payment_method": row_match.group("payment_method"),
        },
        fallback_department=fallback_department,
        raw_values=[
            row_match.group("date"),
            row_match.group("time"),
            place,
            purpose,
            party_size,
            row_match.group("amount"),
            row_match.group("payment_method"),
        ],
    )


def _parse_pdf_text_region_amount_place_purpose_line(
    line: str,
    *,
    fallback_department: str,
) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_REGION_AMOUNT_PLACE_PURPOSE_ROW_RE.match(line)
    if not row_match:
        return None
    place, purpose = _split_place_and_purpose_by_columns(row_match.group("body").strip())
    if not place or not purpose:
        return None
    party_size = row_match.group("party_size")
    if party_size == "-":
        party_size = None
    return _build_pdf_row(
        {
            "used_at": f"{row_match.group('date')} {row_match.group('time')}",
            "place_name": place,
            "purpose": purpose,
            "amount": row_match.group("amount"),
            "party_size": party_size,
            "user_text": row_match.group("user").strip(),
            "payment_method": row_match.group("payment_method"),
        },
        fallback_department=fallback_department,
        raw_values=[
            row_match.group("region"),
            row_match.group("date"),
            row_match.group("time"),
            place,
            purpose,
            party_size,
            row_match.group("amount"),
            row_match.group("payment_method"),
            row_match.group("user"),
        ],
    )


def _parse_pdf_text_optional_user_place_purpose_amount_line(
    line: str,
    *,
    fallback_department: str,
) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_OPTIONAL_USER_PLACE_PURPOSE_AMOUNT_ROW_RE.match(line)
    if not row_match:
        return None
    place, purpose = _split_place_and_purpose_by_marker(row_match.group("body").strip())
    if not place or not purpose:
        return None
    party_size = row_match.group("party_size")
    if party_size == "-":
        party_size = None
    return _build_pdf_row(
        {
            "used_at": f"{row_match.group('date')} {row_match.group('time')}",
            "place_name": place,
            "purpose": purpose,
            "amount": row_match.group("amount"),
            "party_size": party_size,
            "user_text": (row_match.group("user") or fallback_department).strip(),
            "payment_method": row_match.group("payment_method"),
            "expense_category": row_match.group("expense_category"),
        },
        fallback_department=fallback_department,
        raw_values=[
            row_match.group("user"),
            row_match.group("date"),
            row_match.group("time"),
            place,
            purpose,
            party_size,
            row_match.group("amount"),
            row_match.group("payment_method"),
            row_match.group("expense_category"),
        ],
    )


def _parse_pdf_text_user_amount_place_address_purpose_line(
    line: str,
    *,
    fallback_department: str,
) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_USER_AMOUNT_PLACE_ADDRESS_PURPOSE_ROW_RE.match(line)
    if not row_match:
        return None
    place, address, purpose = _split_place_address_and_purpose(row_match.group("body").strip())
    if not place or not purpose:
        return None
    party_size = row_match.group("party_size")
    if party_size == "-":
        party_size = None
    return _build_pdf_row(
        {
            "used_at": f"{row_match.group('date')} {row_match.group('time')}",
            "place_name": place,
            "address": address,
            "purpose": purpose,
            "amount": row_match.group("amount"),
            "party_size": party_size,
            "user_text": row_match.group("user").strip(),
            "payment_method": row_match.group("payment_method"),
            "expense_category": None,
        },
        fallback_department=fallback_department,
        raw_values=[
            row_match.group("user"),
            row_match.group("date"),
            row_match.group("time"),
            place,
            address,
            purpose,
            row_match.group("target"),
            party_size,
            row_match.group("amount"),
            row_match.group("payment_method"),
        ],
    )


def _parse_pdf_text_user_place_purpose_amount_line(
    line: str,
    *,
    fallback_department: str,
) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_USER_PLACE_PURPOSE_AMOUNT_ROW_RE.match(line)
    if not row_match:
        return None
    place, purpose = _split_place_and_purpose_by_marker(row_match.group("body").strip())
    if not place or not purpose:
        return None
    party_size = row_match.group("party_size")
    if party_size == "-":
        party_size = None
    return _build_pdf_row(
        {
            "used_at": f"{row_match.group('date')} {row_match.group('time')}",
            "place_name": place,
            "purpose": purpose,
            "amount": row_match.group("amount"),
            "party_size": party_size,
            "user_text": row_match.group("user").strip(),
            "payment_method": row_match.group("payment_method"),
        },
        fallback_department=fallback_department,
        raw_values=[
            row_match.group("user"),
            row_match.group("date"),
            row_match.group("time"),
            place,
            purpose,
            row_match.group("amount"),
            party_size,
            row_match.group("payment_method"),
        ],
    )


def _parse_pdf_text_user_amount_purpose_line(line: str, *, fallback_department: str) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_USER_AMOUNT_PURPOSE_ROW_RE.match(line)
    if not row_match:
        return None
    party_size = row_match.group("party_size")
    if party_size == "-":
        party_size = None
    return _build_pdf_row(
        {
            "used_at": f"{row_match.group('date')} {row_match.group('time')}",
            "place_name": row_match.group("place").strip(),
            "purpose": row_match.group("purpose").strip(),
            "amount": row_match.group("amount"),
            "party_size": party_size,
            "user_text": row_match.group("user").strip(),
            "payment_method": row_match.group("payment_method"),
            "expense_category": row_match.group("expense_category"),
        },
        fallback_department=fallback_department,
        raw_values=[
            row_match.group("user"),
            row_match.group("date"),
            row_match.group("time"),
            row_match.group("place"),
            row_match.group("amount"),
            row_match.group("purpose"),
            party_size,
            row_match.group("payment_method"),
            row_match.group("expense_category"),
        ],
    )


def _parse_pdf_text_user_no_address_line(line: str, *, fallback_department: str) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_USER_NO_ADDRESS_ROW_RE.match(line)
    if not row_match:
        return None
    place, purpose = _split_place_and_purpose(row_match.group("body").strip(), row_match.group("user").strip())
    if not place or not purpose:
        return None
    party_size = re.sub(r"\D", "", row_match.group("party_size"))
    return _build_pdf_row(
        {
            "used_at": f"{row_match.group('date')} {row_match.group('time')}",
            "place_name": place,
            "purpose": purpose,
            "amount": row_match.group("amount"),
            "party_size": party_size,
            "user_text": "구의원",
            "payment_method": row_match.group("payment_method"),
            "expense_category": row_match.group("expense_category"),
        },
        fallback_department=fallback_department,
        raw_values=[
            row_match.group("user"),
            row_match.group("date"),
            row_match.group("time"),
            place,
            purpose,
            row_match.group("party_size"),
            row_match.group("amount"),
            row_match.group("payment_method"),
            row_match.group("expense_category"),
        ],
    )


def _split_place_and_purpose(body: str, user: str) -> tuple[str, str]:
    parts = [part.strip() for part in re.split(r"\s{2,}", body, maxsplit=1) if part.strip()]
    if len(parts) == 2:
        return parts[0], parts[1]
    for marker in (user, *PDF_TEXT_PURPOSE_STARTERS):
        marker = marker.strip()
        if not marker:
            continue
        index = body.find(marker)
        if index > 0:
            return body[:index].strip(), body[index:].strip()
    return "", ""


def _split_purpose_and_place(body: str) -> tuple[str, str]:
    parts = [_normalize_pdf_text_fragment(part) for part in re.split(r"\s{2,}", body) if part.strip()]
    if len(parts) < 2:
        return "", ""
    return parts[0], " ".join(parts[1:])


def _split_place_and_purpose_by_columns(body: str) -> tuple[str, str]:
    parts = [_normalize_pdf_text_fragment(part) for part in re.split(r"\s{2,}", body, maxsplit=1) if part.strip()]
    if len(parts) == 2:
        return parts[0], parts[1]
    return _split_place_and_purpose_by_marker(body)


def _split_place_and_purpose_by_marker(body: str) -> tuple[str, str]:
    for marker in PDF_TEXT_PURPOSE_STARTERS:
        index = body.find(marker)
        if index > 0:
            place = _clean_pdf_place_fragment(body[:index])
            return place, _normalize_pdf_text_fragment(body[index:])
    for pattern in PDF_TEXT_PURPOSE_STARTER_PATTERNS:
        match = pattern.search(body)
        if match and match.start() > 0:
            place = _clean_pdf_place_fragment(body[: match.start()])
            return place, _normalize_pdf_text_fragment(body[match.start() :])
    return "", ""


def _split_place_address_and_purpose(body: str) -> tuple[str, str, str]:
    place_and_address, purpose = _split_place_and_purpose_by_marker(body)
    if not place_and_address or not purpose:
        return "", "", ""
    place, address = _split_place_and_address(place_and_address)
    return place, address, purpose


def _split_place_and_address(value: str) -> tuple[str, str]:
    tokens = _normalize_pdf_text_fragment(value).split()
    for index, token in enumerate(tokens[1:], start=1):
        if _looks_like_korean_address_token(token):
            return " ".join(tokens[:index]), " ".join(tokens[index:])
    return _normalize_pdf_text_fragment(value), ""


def _looks_like_korean_address_token(value: str) -> bool:
    compact = value.strip()
    return bool(re.search(r"(?:로|길|대로)\d|(?:동|가)\d|^\d", compact))


def _normalize_pdf_text_fragment(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _clean_pdf_place_fragment(value: str) -> str:
    normalized = _normalize_pdf_text_fragment(value)
    return re.sub(r"\s+(?:의원|담당자)$", "", normalized).strip()


def _parse_pdf_text_purpose_first_line(line: str, *, fallback_department: str) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_PURPOSE_FIRST_ROW_RE.match(line)
    if not row_match:
        return None
    party_size = row_match.group("party_size")
    if party_size == "-":
        party_size = None
    return _build_pdf_row(
        {
            "used_at": f"{row_match.group('date')} {row_match.group('time')}",
            "place_name": row_match.group("place_text").strip(),
            "purpose": row_match.group("purpose").strip(),
            "amount": row_match.group("amount"),
            "party_size": party_size,
            "user_text": fallback_department,
            "payment_method": row_match.group("payment_method"),
        },
        fallback_department=fallback_department,
        raw_values=[
            row_match.group("date"),
            row_match.group("time"),
            row_match.group("place_text"),
            row_match.group("purpose"),
            row_match.group("amount"),
            party_size,
            row_match.group("payment_method"),
        ],
    )


def _parse_segmented_office_pdf_text(text: str, *, fallback_department: str) -> list[ParsedExpenseRow]:
    rows: list[ParsedExpenseRow] = []
    segments = _split_pdf_blank_line_segments(text.splitlines())
    index = 0
    while index < len(segments) - 1:
        if not _looks_like_segmented_row_number(segments[index]) or not PDF_TEXT_SEGMENTED_OFFICE_USER_DATE_RE.match(
            segments[index + 1]
        ):
            index += 1
            continue
        start = index + 1
        end = len(segments)
        for candidate in range(start + 1, len(segments) - 1):
            if _looks_like_segmented_row_number(segments[candidate]) and PDF_TEXT_SEGMENTED_OFFICE_USER_DATE_RE.match(
                segments[candidate + 1]
            ):
                end = candidate
                break
        parsed = _parse_segmented_office_segments(segments[start:end], fallback_department=fallback_department)
        if parsed:
            rows.append(parsed)
        index = end
    return rows


def _parse_user_place_purpose_layout_pdf_text(text: str, *, fallback_department: str) -> list[ParsedExpenseRow]:
    if not all(keyword in text for keyword in ("집행장소", "집행목적", "대상인원", "결제방법")):
        return []
    rows: list[ParsedExpenseRow] = []
    for group in _user_place_purpose_layout_groups(text.splitlines()):
        parsed = _parse_user_place_purpose_layout_group(group, fallback_department=fallback_department)
        if parsed:
            rows.append(parsed)
    return rows


def _user_place_purpose_layout_groups(lines: list[str]) -> list[list[str]]:
    groups: list[list[str]] = []
    current: list[str] = []
    for raw_line in lines:
        line = raw_line.rstrip().replace("\f", "")
        stripped = line.strip()
        if not stripped or stripped == "2026" or stripped.startswith(("연번", "(결제시간)")):
            continue
        if "합계" in stripped:
            if current:
                groups.append(current)
            break
        if PDF_TEXT_LAYOUT_DATE_OR_DASH_RE.search(line):
            if current:
                groups.append(current)
            current = [line]
            continue
        if current:
            current.append(line)
    if current:
        groups.append(current)
    return groups


def _parse_user_place_purpose_layout_group(
    group: list[str],
    *,
    fallback_department: str,
) -> ParsedExpenseRow | None:
    group_text = _normalize_pdf_text_fragment(" ".join(line.strip() for line in group))
    date_match = PDF_TEXT_LAYOUT_DATE_OR_DASH_RE.search(group_text)
    time_match = PDF_TEXT_LAYOUT_TIME_RE.search(group_text)
    amount_match = re.search(
        r"(?P<amount>\d{1,3}(?:,\d{3})+|\d+)\s+"
        r"(?P<party_size>\d+|-)\s+"
        r"(?P<payment_method>신용카드|법인카드|카드|현금|제로페이|계좌이체)",
        group_text,
    )
    row_match = next(
        (
            re.match(r"^\s*(?P<number>\d+)\s+(?P<user>\S+)", line)
            for line in group
            if re.match(r"^\s*\d+\s+\S+", line)
        ),
        None,
    )
    if not date_match or not time_match or not amount_match or not row_match:
        return None
    try:
        used_at = _parse_pdf_date_time(date_match.group(0), time_match.group(0))
        amount = int(amount_match.group("amount").replace(",", ""))
    except ValueError:
        return None

    place_parts: list[str] = []
    purpose_parts: list[str] = []
    amount_value = amount_match.group("amount")
    party_size = amount_match.group("party_size")
    payment_method = amount_match.group("payment_method")
    user = row_match.group("user")
    for line in group:
        for match in re.finditer(r"\S+", line):
            token = match.group(0)
            start = match.start()
            if _layout_token_is_metadata(
                token,
                user=user,
                amount=amount_value,
                party_size=party_size,
                payment_method=payment_method,
            ):
                continue
            if 22 <= start <= 29:
                place_parts.append(token)
            elif 30 <= start < 54:
                purpose_parts.append(token)

    place_text = _normalize_pdf_text_fragment(" ".join(place_parts))
    purpose = _normalize_pdf_text_fragment(" ".join(purpose_parts))
    if not place_text or not purpose:
        return None
    user_text = user
    if party_size and party_size != "-":
        user_text = f"{user_text} {party_size}명"
    return ParsedExpenseRow(
        department_name=fallback_department,
        used_at=used_at.replace(tzinfo=None),
        place_text=place_text,
        purpose=purpose,
        amount=amount,
        user_text=user_text,
        payment_method=payment_method,
        raw_excerpt=" | ".join(
            part
            for part in (
                date_match.group(0),
                time_match.group(0),
                place_text,
                purpose,
                amount_value,
                None if party_size == "-" else party_size,
                payment_method,
            )
            if part
        ),
    )


def _layout_token_is_metadata(
    token: str,
    *,
    user: str,
    amount: str,
    party_size: str,
    payment_method: str,
) -> bool:
    return bool(
        token == user
        or token == amount
        or token == party_size
        or token == payment_method
        or token == "2026"
        or PDF_TEXT_LAYOUT_DATE_OR_DASH_RE.fullmatch(token)
        or PDF_TEXT_LAYOUT_TIME_RE.fullmatch(token)
        or re.fullmatch(r"\d+", token)
    )


def _parse_layout_office_pdf_text(text: str, *, fallback_department: str) -> list[ParsedExpenseRow]:
    lines = text.splitlines()
    header_index = next(
        (
            index
            for index, line in enumerate(lines)
            if "집행일" in line and "집행목적" in line and "집행장소" in line and "집행금액" in line
        ),
        None,
    )
    if header_index is None:
        return []
    positions = _layout_office_header_positions(lines[header_index])
    if not positions:
        return []
    rows: list[ParsedExpenseRow] = []
    for group in _layout_office_row_groups(lines[header_index + 1 :], positions=positions):
        parsed = _parse_layout_office_row(group, positions=positions, fallback_department=fallback_department)
        if parsed:
            rows.append(parsed)
    return rows


def _layout_office_header_positions(header: str) -> dict[str, int]:
    positions = {
        "number": header.find("연번"),
        "date": header.find("집행일"),
        "purpose": header.find("집행목적"),
        "place": header.find("집행장소"),
        "target": header.find("집행대상"),
        "amount": header.find("집행금액"),
        "payment": header.find("집행방법"),
    }
    if not all(value >= 0 for value in positions.values()):
        return {}
    # pdftotext often places row content several cells left of the visual header
    # when Korean table cells span multiple lines. Keep the hard boundaries for
    # place/amount, but widen purpose and target enough to avoid clipping text.
    positions["purpose"] = max(positions["date"] + len("집행일"), positions["purpose"] - 5)
    positions["place"] = max(positions["purpose"] + len("집행목적"), positions["place"] - 1)
    positions["target"] = max(positions["place"] + len("집행장소"), positions["target"] - 1)
    return positions


def _layout_office_row_groups(lines: list[str], *, positions: dict[str, int]) -> list[list[str]]:
    groups: list[list[str]] = []
    current: list[str] | None = None
    pending: list[str] = []
    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip().strip("\f")
        if not stripped or stripped.startswith("(단위"):
            continue
        clean_line = line.replace("\f", "")
        row_start = bool(PDF_TEXT_LAYOUT_ROW_NUMBER_RE.match(clean_line))
        has_date = bool(PDF_TEXT_LAYOUT_DATE_RE.search(clean_line))
        if row_start:
            if current:
                groups.append(current)
            current = [*pending, clean_line]
            pending = []
            continue
        if has_date and current and _layout_office_group_is_complete(current):
            groups.append(current)
            current = None
            pending = [clean_line]
            continue
        if current is None:
            pending.append(clean_line)
            continue
        if _layout_office_group_is_complete(current) and not _layout_office_continues_current_row(
            raw_line,
            positions=positions,
        ):
            pending.append(clean_line)
            continue
        current.append(clean_line)
    if current:
        groups.append(current)
    return groups


def _layout_office_group_is_complete(group: list[str]) -> bool:
    text = " ".join(group)
    return bool(PDF_TEXT_LAYOUT_AMOUNT_RE.search(text) and PDF_TEXT_LAYOUT_PAYMENT_RE.search(text))


def _layout_office_continues_current_row(line: str, *, positions: dict[str, int]) -> bool:
    if "\f" in line or PDF_TEXT_LAYOUT_TIME_RE.search(line):
        return True
    target = _layout_slice(line.replace("\f", ""), positions["target"], positions["amount"])
    return bool(re.search(r"(명|직원|관계자|대상)", target))


def _parse_layout_office_row(
    group: list[str],
    *,
    positions: dict[str, int],
    fallback_department: str,
) -> ParsedExpenseRow | None:
    group_text = _normalize_pdf_text_fragment(" ".join(line.strip().strip("\f") for line in group))
    date_match = PDF_TEXT_LAYOUT_DATE_RE.search(group_text)
    time_match = PDF_TEXT_LAYOUT_TIME_RE.search(group_text)
    amount_matches = list(PDF_TEXT_LAYOUT_AMOUNT_RE.finditer(group_text))
    payment_match = PDF_TEXT_LAYOUT_PAYMENT_RE.search(group_text)
    if not date_match or not time_match or not amount_matches or not payment_match:
        return None
    try:
        used_at = _parse_pdf_date_time(date_match.group(0), time_match.group(0))
        amount = int(amount_matches[-1].group(0).replace(",", ""))
    except ValueError:
        return None

    purpose = _layout_collect_column(group, positions["purpose"], positions["place"])
    place_text = _layout_collect_column(group, positions["place"], positions["target"])
    target_text = _layout_collect_column(group, positions["target"], positions["amount"])
    if not purpose or not place_text:
        return None
    party_size_match = re.search(r"(?P<size>\d{1,3})\s*명", target_text)
    user_text = target_text or fallback_department
    if party_size_match and "명" not in user_text:
        user_text = f"{user_text} {party_size_match.group('size')}명"
    raw_excerpt = " | ".join(
        part
        for part in (
            date_match.group(0),
            time_match.group(0),
            place_text,
            purpose,
            target_text,
            amount_matches[-1].group(0),
            payment_match.group(0),
        )
        if part
    )
    return ParsedExpenseRow(
        department_name=fallback_department,
        used_at=used_at.replace(tzinfo=None),
        place_text=place_text,
        purpose=purpose,
        amount=amount,
        user_text=user_text,
        payment_method=payment_match.group(0),
        raw_excerpt=raw_excerpt,
    )


def _layout_collect_column(group: list[str], start: int, end: int) -> str:
    parts = []
    for line in group:
        value = _layout_slice(line, start, end)
        if not value:
            continue
        value = PDF_TEXT_LAYOUT_ROW_NUMBER_RE.sub("", value).strip()
        value = PDF_TEXT_LAYOUT_DATE_RE.sub("", value)
        value = PDF_TEXT_LAYOUT_TIME_RE.sub("", value)
        value = PDF_TEXT_LAYOUT_AMOUNT_RE.sub("", value)
        value = PDF_TEXT_LAYOUT_PAYMENT_RE.sub("", value)
        value = _normalize_pdf_text_fragment(value)
        if value:
            parts.append(value)
    return _normalize_pdf_text_fragment(" ".join(parts))


def _layout_slice(line: str, start: int, end: int) -> str:
    if len(line) <= start:
        return ""
    return line[start:end].strip()


def _parse_segmented_office_segments(segments: list[str], *, fallback_department: str) -> ParsedExpenseRow | None:
    if len(segments) < 4:
        return None
    user_match_index = None
    user_match: re.Match[str] | None = None
    for index, segment in enumerate(segments):
        user_match = PDF_TEXT_SEGMENTED_OFFICE_USER_DATE_RE.match(segment)
        if user_match:
            user_match_index = index
            break
    if user_match_index is None or user_match is None:
        return None

    payment_index = None
    payment_match: re.Match[str] | None = None
    for index in range(len(segments) - 1, user_match_index, -1):
        payment_match = PDF_TEXT_SEGMENTED_OFFICE_PAYMENT_RE.search(segments[index])
        if payment_match:
            payment_index = index
            break
    if payment_index is None or payment_match is None:
        return None

    amount_index = None
    amount = None
    for index in range(payment_index - 1, user_match_index, -1):
        normalized = segments[index].replace(",", "").strip()
        if re.fullmatch(r"\d+", normalized):
            amount_index = index
            amount = int(normalized)
            break
    if amount_index is None or amount is None:
        return None

    party_size = ""
    content_end = amount_index
    if amount_index - 1 > user_match_index and re.fullmatch(r"\d+\s*명?|-", segments[amount_index - 1].strip()):
        party_size = re.sub(r"\D", "", segments[amount_index - 1])
        content_end = amount_index - 1

    place_tail = (user_match.group("tail") or "").strip()
    content_segments = segments[user_match_index + 1 : content_end]
    if place_tail:
        place_text = place_tail
        purpose_segments = content_segments
    elif content_segments:
        place_text = content_segments[0]
        purpose_segments = content_segments[1:]
    else:
        return None
    purpose = _normalize_pdf_text_fragment(" ".join(purpose_segments))
    if not party_size:
        purpose, party_size = _extract_embedded_party_size(purpose)
    place_text = _normalize_pdf_text_fragment(place_text)
    if not place_text or not purpose:
        return None
    try:
        used_at = _parse_pdf_date_time(user_match.group("date"), user_match.group("time"))
    except ValueError:
        return None
    user_text = user_match.group("user").strip()
    if party_size:
        user_text = f"{user_text} {party_size}명"
    raw_excerpt = " | ".join(
        part
        for part in (
            user_match.group("user"),
            user_match.group("date"),
            user_match.group("time"),
            place_text,
            purpose,
            party_size,
            str(amount),
            payment_match.group("payment_method"),
            payment_match.group("expense_category"),
        )
        if part
    )
    return ParsedExpenseRow(
        department_name=fallback_department,
        used_at=used_at.replace(tzinfo=None),
        place_text=place_text,
        purpose=purpose,
        amount=amount,
        user_text=user_text,
        payment_method=payment_match.group("payment_method"),
        expense_category=payment_match.group("expense_category"),
        raw_excerpt=raw_excerpt,
    )


def _split_pdf_blank_line_segments(lines: list[str]) -> list[str]:
    segments: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip().strip("\f")
        if not stripped:
            if current:
                segments.append(_normalize_pdf_text_fragment(" ".join(current)))
                current = []
            continue
        current.append(stripped)
    if current:
        segments.append(_normalize_pdf_text_fragment(" ".join(current)))
    return segments


def _looks_like_segmented_row_number(segment: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}", segment.strip()))


def _extract_embedded_party_size(purpose: str) -> tuple[str, str]:
    match = re.search(r"\s(?P<party>\d{1,3})\s+(?=경비|비용|간담회|지급|운영|개최)", purpose)
    if not match:
        return purpose, ""
    cleaned = f"{purpose[: match.start()]} {purpose[match.end() :]}".strip()
    return _normalize_pdf_text_fragment(cleaned), match.group("party")


def _parse_pdf_date_time(date_value: str, time_value: str):
    if re.fullmatch(r"20\d{6}", date_value):
        date_value = f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:8]}"
    return date_parser.parse(f"{date_value} {time_value}", fuzzy=True)
