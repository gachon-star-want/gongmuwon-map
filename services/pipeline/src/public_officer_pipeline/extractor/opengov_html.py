from __future__ import annotations

import re
from datetime import date

from selectolax.parser import HTMLParser, Node

from public_officer_pipeline.extractor.rows import RawExpenseFields, build_expense_row
from public_officer_pipeline.models import ParsedExpenseRow
from public_officer_pipeline.extractor.text_utils import normalize_spaces


HEADER_ALIASES = {
    "부서명": "department_name",
    "집행부서": "department_name",
    "사용일시": "used_at",
    "집행일시": "used_at",
    "집행일": "used_at",
    "사용일자": "used_at",
    "사용일자(일시)": "used_at",
    "장소": "place_text",
    "사용장소": "place_text",
    "집행장소": "place_text",
    "사용장소(가맹점명)": "place_text",
    "사용목적": "purpose",
    "집행목적": "purpose",
    "집행유형": "purpose",
    "집행내역": "purpose",
    "결제내용": "purpose",
    "사용목적(내역)": "purpose",
    "집행구분": "expense_category",
    "사용금액(원)": "amount",
    "집행금액(원)": "amount",
    "집행액(천원)": "amount_thousand",
    "금액(천원)": "amount_thousand",
    "집행액": "amount",
    "금액": "amount",
    "사용자 및 인원": "user_text",
    "사용자": "user_text",
    "집행대상": "user_text",
    "참석대상": "user_text",
    "집행인원": "party_size",
    "대상인원": "party_size",
    "대상인원수(명)": "party_size",
    "인원(수량)": "party_size",
    "결제방법": "payment_method",
    "결재방법": "payment_method",
    "사용방법": "payment_method",
    "비목": "expense_category",
    "구분": "expense_category",
}


def extract_expense_rows(html: str, fallback_date: date | None = None) -> list[ParsedExpenseRow]:
    tree = HTMLParser(html)
    rows: list[ParsedExpenseRow] = []
    for table in tree.css("table"):
        keyed = _extract_key_value_table(table)
        if keyed:
            keyed = _with_fallback_date(keyed, fallback_date)
            parsed = _parse_row(keyed, [f"{key}: {value}" for key, value in keyed.items()])
            if parsed:
                rows.append(parsed)
                continue
        table_rows = _extract_table_rows(table)
        if not table_rows:
            continue
        headers = [normalize_spaces(cell) for cell in table_rows[0]]
        mapped_headers = [_map_header(header) for header in headers]
        if ("used_at" not in mapped_headers and fallback_date is None) or "place_text" not in mapped_headers:
            continue
        for raw_row in table_rows[1:]:
            if len(raw_row) < len(headers):
                raw_row = [*raw_row, *[""] * (len(headers) - len(raw_row))]
            item = {
                mapped_headers[index]: normalize_spaces(value)
                for index, value in enumerate(raw_row[: len(mapped_headers)])
                if mapped_headers[index]
            }
            item = _with_fallback_date(item, fallback_date)
            parsed = _parse_row(item, raw_row)
            if parsed:
                rows.append(parsed)
    return rows


def _extract_key_value_table(table: Node) -> dict[str, str]:
    item: dict[str, str] = {}
    for tr in table.css("tr"):
        headers = tr.css("th")
        values = tr.css("td")
        for index, header_cell in enumerate(headers):
            if index >= len(values):
                break
            header = normalize_spaces(header_cell.text(separator=" ", strip=True))
            mapped = _map_header(header)
            if not mapped:
                continue
            value = normalize_spaces(values[index].text(separator=" ", strip=True))
            if value:
                item[mapped] = value
    if "used_at" in item and "place_text" in item and ("amount" in item or "amount_thousand" in item):
        return item
    return {}


def _extract_table_rows(table: Node) -> list[list[str]]:
    rows: list[list[str]] = []
    for tr in table.css("tr"):
        cells = tr.css("th,td")
        if not cells:
            continue
        rows.append([cell.text(separator=" ", strip=True) for cell in cells])
    return rows


def _map_header(header: str) -> str | None:
    compact = re.sub(r"\s+", "", header)
    return HEADER_ALIASES.get(compact)


def _with_fallback_date(item: dict[str, str], fallback_date: date | None) -> dict[str, str]:
    if fallback_date is not None and not item.get("used_at"):
        return {**item, "used_at": fallback_date.isoformat()}
    return item


def _parse_row(item: dict[str, str], raw_row: list[str]) -> ParsedExpenseRow | None:
    amount_text = item.get("amount") or item.get("amount_thousand")
    if not item.get("used_at") or not item.get("place_text") or not amount_text:
        return None

    user_text = item.get("user_text") or None
    return build_expense_row(
        RawExpenseFields(
            department_name=item.get("department_name"),
            used_at=None,
            date_text=item["used_at"],
            place_text=item["place_text"],
            purpose=item.get("purpose") or None,
            amount=amount_text,
            amount_is_thousands=bool(item.get("amount_thousand")),
            party_size=item.get("party_size"),
            user_text=user_text,
            payment_method=item.get("payment_method") or None,
            expense_category=item.get("expense_category") or None,
            raw_values=[value for value in raw_row if normalize_spaces(value)],
        ),
        fallback_department=item.get("department_name") or "서울시본청",
    )


