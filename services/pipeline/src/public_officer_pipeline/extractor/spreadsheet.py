from __future__ import annotations

import re
from datetime import date, datetime, time
from io import BytesIO
from typing import Any

from dateutil import parser as date_parser
from openpyxl import load_workbook

from public_officer_pipeline.models import ParsedExpenseRow


HEADER_ALIASES = {
    "집행일자": "used_date",
    "사용일자": "used_date",
    "사용일": "used_date",
    "일자": "used_date",
    "집행시간": "used_time",
    "사용시간": "used_time",
    "사용시각": "used_time",
    "시각": "used_time",
    "시간": "used_time",
    "사용자": "user_text",
    "집행자": "user_text",
    "구분": "user_text",
    "장소": "place_text",
    "사용장소": "place_text",
    "집행장소": "place_text",
    "집행처": "place_text",
    "집행처명": "place_text",
    "가맹점명": "place_text",
    "상호": "place_text",
    "상호명": "place_text",
    "업소명": "place_text",
    "주소": "address_hint",
    "집행처주소": "address_hint",
    "가맹점주소": "address_hint",
    "집행목적": "purpose",
    "사용목적": "purpose",
    "집행내역": "purpose",
    "내역": "purpose",
    "대상인원수": "party_size",
    "대상인원": "party_size",
    "인원": "party_size",
    "인원수": "party_size",
    "금액": "amount",
    "집행금액": "amount",
    "사용금액": "amount",
    "승인금액": "amount",
    "결제방법": "payment_method",
    "결재방법": "payment_method",
    "집행방법": "payment_method",
    "사용방법": "payment_method",
    "방법": "payment_method",
    "사용방법및비고": "payment_method",
    "비목": "expense_category",
}

DEPARTMENT_RE = re.compile(r"부서명\s*[:：]\s*(?P<department>.+)")


def extract_spreadsheet_rows(content: bytes, *, fallback_department: str) -> list[ParsedExpenseRow]:
    workbook = load_workbook(BytesIO(content), data_only=True, read_only=True)
    rows: list[ParsedExpenseRow] = []
    for worksheet in workbook.worksheets:
        sheet_rows = [[_stringify(cell) for cell in row] for row in worksheet.iter_rows(values_only=True)]
        department = _extract_department(sheet_rows) or fallback_department
        header_index, mapped_headers = _find_header(sheet_rows)
        if header_index is None:
            continue
        for raw_row in sheet_rows[header_index + 1 :]:
            parsed = _parse_row(raw_row, mapped_headers, department)
            if parsed:
                rows.append(parsed)
    return rows


def _extract_department(rows: list[list[str]]) -> str | None:
    for row in rows[:10]:
        text = " ".join(cell for cell in row if cell)
        match = DEPARTMENT_RE.search(text)
        if match:
            return _clean(match.group("department"))
    return None


def _find_header(rows: list[list[str]]) -> tuple[int | None, list[str | None]]:
    for index, row in enumerate(rows[:20]):
        mapped = [_map_header(cell) for cell in row]
        if "used_date" in mapped and "place_text" in mapped and "amount" in mapped:
            return index, mapped
        if index + 1 < len(rows):
            width = max(len(row), len(rows[index + 1]))
            overlaid = [
                (rows[index + 1][column] if column < len(rows[index + 1]) else "")
                or (row[column] if column < len(row) else "")
                for column in range(width)
            ]
            mapped = [_map_header(cell) for cell in overlaid]
            if "used_date" in mapped and "place_text" in mapped and "amount" in mapped:
                return index + 1, mapped
    return None, []


def _map_header(header: str) -> str | None:
    compact = re.sub(r"\s+", "", header)
    normalized = re.sub(r"[（(][^)）]+[)）]", "", compact)
    return HEADER_ALIASES.get(normalized) or HEADER_ALIASES.get(compact)


def _parse_row(raw_row: list[str], mapped_headers: list[str | None], department: str) -> ParsedExpenseRow | None:
    item = {
        mapped_headers[index]: _clean(value)
        for index, value in enumerate(raw_row[: len(mapped_headers)])
        if mapped_headers[index] and _clean(value)
    }
    if not item.get("used_date") or not item.get("place_text") or not item.get("amount"):
        return None
    try:
        used_at = _parse_datetime(item["used_date"], item.get("used_time"))
        amount = int(re.sub(r"[^\d]", "", item["amount"]))
    except (ValueError, TypeError):
        return None
    if amount <= 0:
        return None

    place_text = item["place_text"]
    if item.get("address_hint"):
        place_text = f"{place_text} ({item['address_hint']})"

    user_text = item.get("user_text") or department
    if item.get("party_size"):
        user_text = f"{user_text} {item['party_size']}명"

    return ParsedExpenseRow(
        department_name=department,
        used_at=used_at,
        place_text=place_text,
        purpose=item.get("purpose") or None,
        amount=amount,
        user_text=user_text,
        payment_method=item.get("payment_method") or None,
        expense_category=item.get("expense_category") or None,
        raw_excerpt=" | ".join(_clean(value) for value in raw_row if _clean(value)),
    )


def _parse_datetime(date_value: str, time_value: str | None) -> datetime:
    parsed_date = date_parser.parse(date_value, fuzzy=True).date()
    if not time_value:
        return datetime.combine(parsed_date, time.min)
    parsed_time = date_parser.parse(time_value, fuzzy=True).time()
    return datetime.combine(parsed_date, parsed_time).replace(tzinfo=None)


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    return str(value)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()
