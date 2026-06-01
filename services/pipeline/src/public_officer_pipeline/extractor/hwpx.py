from __future__ import annotations

import re
import zipfile
from io import BytesIO
from xml.etree import ElementTree

from public_officer_pipeline import document_guards as guards
from public_officer_pipeline.extractor.spreadsheet import extract_grid_rows
from public_officer_pipeline.models import ParsedExpenseRow


HWPX_SECTION_RE = re.compile(r"^Contents/section\d+\.xml$")
DEPARTMENT_HINT_RE = re.compile(
    r"[<(（]\s*(?P<department>[가-힣0-9·\s]+(?:담당관|구청장|부구청장|시장|부시장|센터|사업소|보건소|의회사무국|의회사무과|과|팀|국|실|소))\s*[>)）]"
)


def extract_hwpx_rows(content: bytes, *, fallback_department: str) -> list[ParsedExpenseRow]:
    sections = _read_section_xml(content)
    department = _extract_document_department(sections) or fallback_department
    tables = [_table_rows(table) for section in sections for table in _section_tables(section)]
    tables = [table for table in tables if table]
    return extract_grid_rows(tables, fallback_department=department)


def _read_section_xml(content: bytes) -> list[ElementTree.Element]:
    guards.ensure_size_at_most(
        size=len(content),
        max_bytes=guards.MAX_SPREADSHEET_BYTES,
        subject="HWPX document",
    )
    guards.preflight_xlsx_zip(content)
    with zipfile.ZipFile(BytesIO(content)) as archive:
        section_names = sorted(name for name in archive.namelist() if HWPX_SECTION_RE.match(name))
        sections = []
        for name in section_names:
            sections.append(ElementTree.fromstring(archive.read(name)))
    return sections


def _extract_document_department(sections: list[ElementTree.Element]) -> str | None:
    paragraphs: list[str] = []
    for section in sections:
        for paragraph in section.iter():
            if _local_name(paragraph.tag) != "p":
                continue
            text = _node_text(paragraph)
            if text:
                paragraphs.append(text)
            if len(paragraphs) >= 20:
                break
        if len(paragraphs) >= 20:
            break
    for text in paragraphs:
        match = DEPARTMENT_HINT_RE.search(text)
        if match:
            return _normalize_spaces(match.group("department"))
    return None


def _section_tables(section: ElementTree.Element) -> list[ElementTree.Element]:
    return [node for node in section.iter() if _local_name(node.tag) == "tbl"]


def _table_rows(table: ElementTree.Element) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in _direct_children(table, "tr"):
        values: list[str] = []
        for cell in _direct_children(row, "tc"):
            column_index = _cell_column_index(cell)
            if column_index is not None:
                while len(values) < column_index:
                    values.append("")
            text = _node_text(cell)
            values.append(text)
            for _ in range(max(_cell_col_span(cell) - 1, 0)):
                values.append("")
        values = _trim_trailing_empty_cells(values)
        if any(values):
            rows.append(values)
    return rows


def _direct_children(node: ElementTree.Element, local_name: str) -> list[ElementTree.Element]:
    return [child for child in list(node) if _local_name(child.tag) == local_name]


def _cell_column_index(cell: ElementTree.Element) -> int | None:
    addr = next((child for child in list(cell) if _local_name(child.tag) == "cellAddr"), None)
    if addr is None:
        return None
    try:
        return int(addr.attrib.get("colAddr", ""))
    except ValueError:
        return None


def _cell_col_span(cell: ElementTree.Element) -> int:
    span = next((child for child in list(cell) if _local_name(child.tag) == "cellSpan"), None)
    if span is None:
        return 1
    try:
        return max(int(span.attrib.get("colSpan", "1")), 1)
    except ValueError:
        return 1


def _node_text(node: ElementTree.Element) -> str:
    values = [text for child in node.iter() if _local_name(child.tag) == "t" for text in [child.text or ""]]
    return _normalize_spaces(" ".join(values))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _trim_trailing_empty_cells(row_values: list[str]) -> list[str]:
    last_non_empty = -1
    for index, value in enumerate(row_values):
        if value:
            last_non_empty = index
    return row_values[: last_non_empty + 1]


def _normalize_spaces(value: str) -> str:
    return " ".join(value.split())
