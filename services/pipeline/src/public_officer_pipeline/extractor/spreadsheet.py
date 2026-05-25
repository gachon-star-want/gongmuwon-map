from __future__ import annotations

import re
from datetime import date, datetime, time
from io import BytesIO
from typing import Any

import xlrd
from openpyxl import load_workbook

from public_officer_pipeline.extractor.rows import RawExpenseFields, build_expense_row
from public_officer_pipeline.models import ParsedExpenseRow


HEADER_ALIASES = {
    "집행일자": "used_date",
    "집행일": "used_date",
    "사용일자": "used_date",
    "사용일": "used_date",
    "승인일": "used_date",
    "사용일시": "used_date",
    "일시": "used_date",
    "일자": "used_date",
    "집행시간": "used_time",
    "사용시간": "used_time",
    "사용시각": "used_time",
    "승인시각": "used_time",
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
    "집행인원": "party_size",
    "인원": "party_size",
    "인원수": "party_size",
    "결제": "payment_method",
    "금액": "amount",
    "집행금액": "amount",
    "집행액": "amount",
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
    rows: list[ParsedExpenseRow] = []
    for sheet_rows in _workbook_rows(content):
        department = _extract_department(sheet_rows) or fallback_department
        header_index, mapped_headers = _find_header(sheet_rows)
        if header_index is None:
            continue
        for raw_row in sheet_rows[header_index + 1 :]:
            parsed = _parse_row(raw_row, mapped_headers, department)
            if parsed:
                rows.append(parsed)
    return rows


def _workbook_rows(content: bytes) -> list[list[list[str]]]:
    if content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return _xls_workbook_rows(content)
    workbook = load_workbook(BytesIO(content), data_only=True, read_only=True)
    return [
        [[_stringify(cell) for cell in row] for row in worksheet.iter_rows(values_only=True)]
        for worksheet in workbook.worksheets
    ]


def _xls_workbook_rows(content: bytes) -> list[list[list[str]]]:
    workbook = xlrd.open_workbook(file_contents=content)
    worksheets: list[list[list[str]]] = []
    for worksheet in workbook.sheets():
        rows: list[list[str]] = []
        for row_index in range(worksheet.nrows):
            rows.append(
                [
                    _stringify(_xls_cell_value(worksheet.cell(row_index, column_index), workbook.datemode))
                    for column_index in range(worksheet.ncols)
                ]
            )
        worksheets.append(rows)
    return worksheets


def _xls_cell_value(cell: xlrd.sheet.Cell, datemode: int) -> Any:
    if cell.ctype == xlrd.XL_CELL_DATE:
        return xlrd.xldate.xldate_as_datetime(cell.value, datemode)
    return cell.value


def _extract_department(rows: list[list[str]]) -> str | None:
    for row in rows[:10]:
        text = " ".join(cell for cell in row if cell)
        match = DEPARTMENT_RE.search(text)
        if match:
            return _clean(match.group("department"))
    return None


def _find_header(rows: list[list[str]]) -> tuple[int | None, list[str | None]]:
    for index, row in enumerate(rows[:20]):
        mapped = _disambiguate_headers(row, [_map_header(cell) for cell in row])
        has_place_hint = "place_text" in mapped or "purpose" in mapped or "expense_category" in mapped
        if "used_date" in mapped and has_place_hint and "amount" in mapped:
            return index, mapped
        if index + 1 < len(rows):
            width = max(len(row), len(rows[index + 1]))
            overlaid = [
                (rows[index + 1][column] if column < len(rows[index + 1]) else "")
                or (row[column] if column < len(row) else "")
                for column in range(width)
            ]
            mapped = _disambiguate_headers(overlaid, [_map_header(cell) for cell in overlaid])
            has_place_hint = "place_text" in mapped or "purpose" in mapped or "expense_category" in mapped
            if "used_date" in mapped and has_place_hint and "amount" in mapped:
                return index + 1, mapped
    return None, []


def _map_header(header: str) -> str | None:
    compact = re.sub(r"\s+", "", header)
    normalized = re.sub(r"[（(][^)）]+[)）]", "", compact)
    return HEADER_ALIASES.get(normalized) or HEADER_ALIASES.get(compact)


def _disambiguate_headers(raw_headers: list[str], mapped_headers: list[str | None]) -> list[str | None]:
    mapped = list(mapped_headers)
    compact = [re.sub(r"\s+", "", header) for header in raw_headers]
    if "사용자" in compact and compact and compact[0] == "구분":
        mapped[0] = "expense_category"
    execution_type_indexes = [index for index, header in enumerate(compact) if header == "집행유형"]
    if len(execution_type_indexes) >= 2:
        mapped[execution_type_indexes[0]] = "purpose"
        mapped[execution_type_indexes[-1]] = "payment_method"
    elif len(execution_type_indexes) == 1:
        mapped[execution_type_indexes[0]] = "purpose"
    return mapped


def _parse_row(raw_row: list[str], mapped_headers: list[str | None], department: str) -> ParsedExpenseRow | None:
    item = {
        mapped_headers[index]: _clean(value)
        for index, value in enumerate(raw_row[: len(mapped_headers)])
        if mapped_headers[index] and _clean(value)
    }
    place_text = item.get("place_text") or item.get("purpose") or item.get("expense_category")
    if not item.get("used_date") or not place_text or not item.get("amount"):
        return None

    user_text = item.get("user_text") or department
    amount_text = item.get("amount")
    return build_expense_row(
        RawExpenseFields(
            department_name=department,
            date_text=item["used_date"],
            time_text=item.get("used_time"),
            place_name=place_text,
            address=item.get("address_hint"),
            purpose=item.get("purpose") or None,
            amount=amount_text,
            party_size=item.get("party_size"),
            user_text=user_text,
            payment_method=item.get("payment_method") or None,
            expense_category=item.get("expense_category") or None,
            raw_values=raw_row,
        ),
        fallback_department=department,
        address_separator=" (",
    )


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    return str(value)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()
