from __future__ import annotations

import re
import zipfile
from datetime import date, datetime, time
from io import BytesIO
from typing import Any
from xml.etree import ElementTree

import xlrd
from openpyxl import load_workbook
from selectolax.parser import HTMLParser

from public_officer_pipeline import document_guards as guards
from public_officer_pipeline.extractor.rows import RawExpenseFields, build_expense_row
from public_officer_pipeline.models import ParsedExpenseRow


HEADER_ALIASES = {
    "집행일자": "used_date",
    "집행일": "used_date",
    "사용일자": "used_date",
    "사용일": "used_date",
    "승인일": "used_date",
    "사용일시": "used_date",
    "집행일시": "used_date",
    "일시": "used_date",
    "일자": "used_date",
    "일": "used_date",
    "집행시간": "used_time",
    "사용시간": "used_time",
    "사용시각": "used_time",
    "승인시각": "used_time",
    "시각": "used_time",
    "시간": "used_time",
    "시": "used_time",
    "사용자": "user_text",
    "집행자": "user_text",
    "구분": "user_text",
    "장소": "place_text",
    "사용장소": "place_text",
    "집행장소": "place_text",
    "집행처": "place_text",
    "집행처명": "place_text",
    "사용처": "place_text",
    "가맹점명": "place_text",
    "상호": "place_text",
    "상호명": "place_text",
    "업소명": "place_text",
    "주소": "address_hint",
    "집행처주소": "address_hint",
    "가맹점주소": "address_hint",
    "집행목적": "purpose",
    "사용목적": "purpose",
    "사용내역": "purpose",
    "집행내역": "purpose",
    "내역": "purpose",
    "대상인원수": "party_size",
    "대상인원": "party_size",
    "집행인원": "party_size",
    "참석자": "party_size",
    "인원": "party_size",
    "인원수": "party_size",
    "결제": "payment_method",
    "금액": "amount",
    "집행금액": "amount",
    "집행액": "amount",
    "사용금액": "amount",
    "승인금액": "amount",
    "지출액": "amount",
    "지출금액": "amount",
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
    return extract_grid_rows(_workbook_rows(content), fallback_department=fallback_department)


def extract_grid_rows(
    grid_rows: list[list[list[str]]],
    *,
    fallback_department: str,
) -> list[ParsedExpenseRow]:
    rows: list[ParsedExpenseRow] = []
    for sheet_rows in grid_rows:
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
    guards.ensure_size_at_most(
        size=len(content),
        max_bytes=guards.MAX_SPREADSHEET_BYTES,
        subject="spreadsheet document",
    )
    if content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return _xls_workbook_rows(content)
    try:
        guards.preflight_xlsx_zip(content)
    except zipfile.BadZipFile:
        html_rows = _html_table_rows(content)
        if html_rows:
            return html_rows
        raise
    workbook = _load_xlsx_workbook(content)
    try:
        worksheets = workbook.worksheets[: guards.MAX_SPREADSHEET_SHEETS]
        workbook_rows: list[list[list[str]]] = []
        total_cells = 0
        for worksheet in worksheets:
            sheet_rows: list[list[str]] = []
            empty_run = 0
            non_empty_row_count = 0
            for row_index, row in enumerate(worksheet.iter_rows(values_only=True), start=1):
                row_values = _trim_trailing_empty_cells([_stringify(cell) for cell in row])
                if not any(row_values):
                    empty_run += 1
                    if sheet_rows and empty_run >= guards.MAX_SPREADSHEET_ROWS_PER_SHEET:
                        break
                    continue
                empty_run = 0
                non_empty_row_count += 1
                if non_empty_row_count > guards.MAX_SPREADSHEET_ROWS_PER_SHEET:
                    raise guards.DocumentProcessingLimitError(
                        f"spreadsheet sheet {worksheet.title!r} rows count exceeds limit of "
                        f"{guards.MAX_SPREADSHEET_ROWS_PER_SHEET}"
                    )
                total_cells += _checked_row_width(
                    sheet_name=worksheet.title,
                    row_index=non_empty_row_count,
                    width=len(row_values),
                    current_total_cells=total_cells,
                )
                sheet_rows.append(row_values)
            workbook_rows.append(sheet_rows)
        return workbook_rows
    finally:
        workbook.close()


def _trim_trailing_empty_cells(row_values: list[str]) -> list[str]:
    last_non_empty = -1
    for index, value in enumerate(row_values):
        if value:
            last_non_empty = index
    return row_values[: last_non_empty + 1]


def _load_xlsx_workbook(content: bytes):
    try:
        return load_workbook(BytesIO(content), data_only=True, read_only=True)
    except TypeError as exc:
        message = str(exc)
        if "_NamedCellStyle" not in message or "name should be" not in message:
            raise
        repaired = _repair_xlsx_missing_cell_style_names(content)
        if repaired == content:
            raise
        return load_workbook(BytesIO(repaired), data_only=True, read_only=True)


def _repair_xlsx_missing_cell_style_names(content: bytes) -> bytes:
    with zipfile.ZipFile(BytesIO(content)) as source:
        if "xl/styles.xml" not in source.namelist():
            return content
        repaired_styles = _repair_styles_xml_missing_cell_style_names(source.read("xl/styles.xml"))
        if repaired_styles is None:
            return content
        output = BytesIO()
        with zipfile.ZipFile(output, "w") as target:
            for item in source.infolist():
                data = repaired_styles if item.filename == "xl/styles.xml" else source.read(item.filename)
                target.writestr(item, data)
    return output.getvalue()


def _repair_styles_xml_missing_cell_style_names(styles_xml: bytes) -> bytes | None:
    try:
        root = ElementTree.fromstring(styles_xml)
    except ElementTree.ParseError:
        return None

    namespace = root.tag[1:].split("}", 1)[0] if root.tag.startswith("{") else ""
    cell_style_tag = f"{{{namespace}}}cellStyle" if namespace else "cellStyle"
    existing_names = {element.attrib["name"] for element in root.iter(cell_style_tag) if element.attrib.get("name")}
    repaired = False
    for index, element in enumerate(root.iter(cell_style_tag), start=1):
        if element.attrib.get("name"):
            continue
        base_name = _builtin_cell_style_name(element.attrib.get("builtinId")) or f"Recovered Style {index}"
        name = _unique_cell_style_name(base_name, existing_names)
        element.set("name", name)
        existing_names.add(name)
        repaired = True
    if not repaired:
        return None
    return ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)


def _builtin_cell_style_name(builtin_id: str | None) -> str | None:
    return {
        "0": "Normal",
        "3": "Comma",
        "4": "Currency",
        "5": "Percent",
        "6": "Comma [0]",
        "7": "Currency [0]",
    }.get(builtin_id or "")


def _unique_cell_style_name(base_name: str, existing_names: set[str]) -> str:
    if base_name not in existing_names:
        return base_name
    suffix = 2
    while f"{base_name} {suffix}" in existing_names:
        suffix += 1
    return f"{base_name} {suffix}"


def _xls_workbook_rows(content: bytes) -> list[list[list[str]]]:
    workbook = xlrd.open_workbook(file_contents=content)
    worksheets: list[list[list[str]]] = []
    total_cells = 0
    for worksheet in workbook.sheets()[: guards.MAX_SPREADSHEET_SHEETS]:
        total_cells = _ensure_declared_sheet_bounds(
            sheet_name=worksheet.name,
            rows=worksheet.nrows,
            columns=worksheet.ncols,
            current_total_cells=total_cells,
        )
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


def _html_table_rows(content: bytes) -> list[list[list[str]]]:
    text = _decode_htmlish_content(content)
    if "<table" not in text.lower():
        return []

    tree = HTMLParser(text)
    tables: list[list[list[str]]] = []
    total_cells = 0
    for table_index, table in enumerate(tree.css("table"), start=1):
        if table_index > guards.MAX_SPREADSHEET_SHEETS:
            break
        sheet_name = f"html table {table_index}"
        rows: list[list[str]] = []
        for tr in table.css("tr"):
            row_values = _trim_trailing_empty_cells(
                [_clean(cell.text(separator=" ", strip=True)) for cell in tr.css("th,td")]
            )
            if not any(row_values):
                continue
            row_index = len(rows) + 1
            if row_index > guards.MAX_SPREADSHEET_ROWS_PER_SHEET:
                raise guards.DocumentProcessingLimitError(
                    f"spreadsheet sheet {sheet_name!r} rows count exceeds limit of "
                    f"{guards.MAX_SPREADSHEET_ROWS_PER_SHEET}"
                )
            total_cells += _checked_row_width(
                sheet_name=sheet_name,
                row_index=row_index,
                width=len(row_values),
                current_total_cells=total_cells,
            )
            rows.append(row_values)
        if rows:
            tables.append(rows)
    return tables


def _decode_htmlish_content(content: bytes) -> str:
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _ensure_declared_sheet_bounds(
    *,
    sheet_name: str,
    rows: int,
    columns: int,
    current_total_cells: int,
) -> int:
    if rows > guards.MAX_SPREADSHEET_ROWS_PER_SHEET:
        raise guards.DocumentProcessingLimitError(
            f"spreadsheet sheet {sheet_name!r} has {rows} rows, "
            f"exceeding limit of {guards.MAX_SPREADSHEET_ROWS_PER_SHEET}"
        )
    if columns > guards.MAX_SPREADSHEET_COLUMNS_PER_SHEET:
        raise guards.DocumentProcessingLimitError(
            f"spreadsheet sheet {sheet_name!r} has {columns} columns, "
            f"exceeding limit of {guards.MAX_SPREADSHEET_COLUMNS_PER_SHEET}"
        )
    total_cells = current_total_cells + (rows * columns)
    if total_cells > guards.MAX_SPREADSHEET_CELLS_TOTAL:
        raise guards.DocumentProcessingLimitError(
            f"spreadsheet workbook has {total_cells} declared cells, "
            f"exceeding limit of {guards.MAX_SPREADSHEET_CELLS_TOTAL}"
        )
    return total_cells


def _checked_row_width(
    *,
    sheet_name: str,
    row_index: int,
    width: int,
    current_total_cells: int,
) -> int:
    if row_index > guards.MAX_SPREADSHEET_ROWS_PER_SHEET:
        raise guards.DocumentProcessingLimitError(
            f"spreadsheet sheet {sheet_name!r} rows count exceeds limit of "
            f"{guards.MAX_SPREADSHEET_ROWS_PER_SHEET}"
        )
    if width > guards.MAX_SPREADSHEET_COLUMNS_PER_SHEET:
        raise guards.DocumentProcessingLimitError(
            f"spreadsheet sheet {sheet_name!r} row {row_index} has {width} columns, "
            f"exceeding limit of {guards.MAX_SPREADSHEET_COLUMNS_PER_SHEET}"
        )
    if current_total_cells + width > guards.MAX_SPREADSHEET_CELLS_TOTAL:
        raise guards.DocumentProcessingLimitError(
            f"spreadsheet workbook cells count exceeds limit of "
            f"{guards.MAX_SPREADSHEET_CELLS_TOTAL}"
        )
    return width


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
        if index + 1 < len(rows):
            width = max(len(row), len(rows[index + 1]))
            overlaid = [
                (rows[index + 1][column] if column < len(rows[index + 1]) else "")
                or (row[column] if column < len(row) else "")
                for column in range(width)
            ]
            overlaid_mapped = _disambiguate_headers(overlaid, [_map_header(cell) for cell in overlaid])
            if (
                any(mapped)
                and _has_required_headers(overlaid_mapped)
                and _header_score(overlaid_mapped) >= _header_score(mapped)
            ):
                return index + 1, overlaid_mapped
        if _has_required_headers(mapped):
            return index, mapped
    return None, []


def _has_required_headers(mapped: list[str | None]) -> bool:
    has_place_hint = "place_text" in mapped or "purpose" in mapped or "expense_category" in mapped
    return "used_date" in mapped and has_place_hint and "amount" in mapped


def _header_score(mapped: list[str | None]) -> int:
    return sum(1 for header in mapped if header)


def _map_header(header: str) -> str | None:
    compact = re.sub(r"\s+", "", header)
    normalized = re.sub(r"[（(][^)）]+[)）]", "", compact)
    if normalized.startswith(("집행목적", "사용목적", "집행내역")):
        return "purpose"
    if normalized.startswith(("사용장소", "집행장소")):
        return "place_text"
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
