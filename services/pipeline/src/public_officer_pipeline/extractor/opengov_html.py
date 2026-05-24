from __future__ import annotations

import re
from datetime import datetime

from dateutil import parser as date_parser
from selectolax.parser import HTMLParser, Node

from public_officer_pipeline.models import ParsedExpenseRow


HEADER_ALIASES = {
    "부서명": "department_name",
    "집행부서": "department_name",
    "사용일시": "used_at",
    "집행일시": "used_at",
    "사용장소": "place_text",
    "집행장소": "place_text",
    "사용목적": "purpose",
    "집행목적": "purpose",
    "집행내역": "purpose",
    "사용금액(원)": "amount",
    "집행금액(원)": "amount",
    "사용자 및 인원": "user_text",
    "사용자": "user_text",
    "집행대상": "user_text",
    "대상인원수(명)": "party_size",
    "결제방법": "payment_method",
    "결재방법": "payment_method",
    "비목": "expense_category",
}


def extract_expense_rows(html: str) -> list[ParsedExpenseRow]:
    tree = HTMLParser(html)
    rows: list[ParsedExpenseRow] = []
    for table in tree.css("table"):
        keyed = _extract_key_value_table(table)
        if keyed:
            parsed = _parse_row(keyed, [f"{key}: {value}" for key, value in keyed.items()])
            if parsed:
                rows.append(parsed)
                continue
        table_rows = _extract_table_rows(table)
        if not table_rows:
            continue
        headers = [_clean(cell) for cell in table_rows[0]]
        mapped_headers = [_map_header(header) for header in headers]
        if "used_at" not in mapped_headers or "place_text" not in mapped_headers:
            continue
        for raw_row in table_rows[1:]:
            if len(raw_row) < len(headers):
                raw_row = [*raw_row, *[""] * (len(headers) - len(raw_row))]
            item = {
                mapped_headers[index]: _clean(value)
                for index, value in enumerate(raw_row[: len(mapped_headers)])
                if mapped_headers[index]
            }
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
            header = _clean(header_cell.text(separator=" ", strip=True))
            mapped = _map_header(header)
            if not mapped:
                continue
            value = _clean(values[index].text(separator=" ", strip=True))
            if value:
                item[mapped] = value
    if "used_at" in item and "place_text" in item and "amount" in item:
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


def _parse_row(item: dict[str, str], raw_row: list[str]) -> ParsedExpenseRow | None:
    if not item.get("used_at") or not item.get("place_text") or not item.get("amount"):
        return None
    try:
        used_at = date_parser.parse(item["used_at"], fuzzy=True)
        amount = int(re.sub(r"[^\d]", "", item["amount"]))
    except (ValueError, TypeError):
        return None
    if amount <= 0:
        return None
    user_text = item.get("user_text") or None
    if user_text and item.get("party_size"):
        user_text = f"{user_text} {item['party_size']}명"
    elif item.get("party_size"):
        user_text = f"{item['party_size']}명"

    return ParsedExpenseRow(
        department_name=item.get("department_name") or "서울시본청",
        used_at=_strip_tz(used_at),
        place_text=item["place_text"],
        purpose=item.get("purpose") or None,
        amount=amount,
        user_text=user_text,
        payment_method=item.get("payment_method") or None,
        expense_category=item.get("expense_category") or None,
        raw_excerpt=" | ".join(_clean(value) for value in raw_row if _clean(value)),
    )


def _strip_tz(value: datetime) -> datetime:
    return value.replace(tzinfo=None)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()
