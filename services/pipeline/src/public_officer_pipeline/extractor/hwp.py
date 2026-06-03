from __future__ import annotations

import re
import shutil
import struct
import subprocess
import tempfile
import unicodedata
import zlib
from datetime import date
from io import BytesIO
from pathlib import Path

import olefile

from public_officer_pipeline import document_guards as guards
from public_officer_pipeline.extractor.rows import RawExpenseFields, build_expense_row
from public_officer_pipeline.extractor.spreadsheet import extract_spreadsheet_rows
from public_officer_pipeline.models import ParsedExpenseRow, PipelineConfigError


HWP5_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
HWP_SIGNATURE = b"HWP Document File"
HWPTAG_PARA_TEXT = 67
EXTENDED_RECORD_SIZE = 0xFFF
HWP_COMPRESSED_FLAG = 0x1

TITLE_MONTH_RE = re.compile(
    r"(?:'(?P<short_year>\d{2})\.\s*(?P<short_month>\d{1,2})월)|"
    r"(?P<year>20\d{2})\s*(?:년|[./-])\s*(?P<month>\d{1,2})\s*월?"
)
FULL_DATE_RE = re.compile(r"^(?:20\d{2}|\d{2})[./-]\d{1,2}[./-]\d{1,2}$")
BARE_NUMBER_RE = re.compile(r"^\d{1,3}$")
AMOUNT_RE = re.compile(r"^(?:\d{1,3}(?:,\d{3})+|\d{4,})$")
TIME_RE = re.compile(r"^(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$")
PAYMENT_RE = re.compile(r"(카드|현금|계좌|이체|제로페이|지출)")
CATEGORY_RE = re.compile(r"^(기관|시책|부서|의정|업무|운영)")
PURPOSE_START_RE = re.compile(
    r"(20\d{2}년|격려|간담|구입|제공|업무|회의|추진|홍보|민원|현안|협의|"
    r"행사|직원|근무|관계자|행정|통합|도정|본회의|특별법|박람회|경조사|"
    r"언론|인터뷰|착공식|타운홀|지방도|이동간|수행|내방객|오찬|만찬|소통|"
    r"의견|설명|방문|대응|지원|간식|다과|물품|지급)"
)


def extract_hwp_rows(
    content: bytes,
    *,
    fallback_department: str,
    source_title: str | None = None,
) -> list[ParsedExpenseRow]:
    guards.ensure_size_at_most(
        size=len(content),
        max_bytes=guards.MAX_DOCUMENT_DOWNLOAD_BYTES,
        subject="HWP document",
    )
    if not content.startswith(HWP5_OLE_MAGIC):
        raise PipelineConfigError("HWP extractor requires a binary HWP 5.x OLE document")

    rows = _extract_hwp_rows_from_records(
        content,
        fallback_department=fallback_department,
        source_title=source_title,
    )
    if rows:
        return rows

    html = _convert_hwp_to_html(content)
    return extract_spreadsheet_rows(html, fallback_department=fallback_department)


def _extract_hwp_rows_from_records(
    content: bytes,
    *,
    fallback_department: str,
    source_title: str | None,
) -> list[ParsedExpenseRow]:
    items = _hwp_text_items(content)
    if not items:
        items = _preview_text_items(content)
    if not items:
        return []

    year, _month = _document_year_month(items, source_title)
    rows = _expense_rows_from_text_items(
        items,
        fallback_department=fallback_department,
        fallback_year=year,
    )
    return _deduplicate_rows(rows)


def _hwp_text_items(content: bytes) -> list[str]:
    try:
        document = olefile.OleFileIO(BytesIO(content))
    except OSError:
        return []

    with document:
        if not document.exists("FileHeader"):
            return []
        header = document.openstream("FileHeader").read()
        if not header.startswith(HWP_SIGNATURE):
            return []
        flags = _hwp_flags(header)
        streams = _body_text_streams(document)
        items: list[str] = []
        for stream_name in streams:
            data = document.openstream(stream_name).read()
            if flags & HWP_COMPRESSED_FLAG:
                data = _decompress_hwp_stream(data)
            items.extend(_text_items_from_records(data))
        return items


def _hwp_flags(header: bytes) -> int:
    if len(header) < 40:
        return 0
    return struct.unpack_from("<I", header, 36)[0]


def _body_text_streams(document: olefile.OleFileIO) -> list[str]:
    streams = [
        "/".join(path)
        for path in document.listdir()
        if len(path) == 2 and path[0] == "BodyText" and path[1].startswith("Section")
    ]

    def sort_key(stream_name: str) -> tuple[int, str]:
        match = re.search(r"Section(?P<index>\d+)$", stream_name)
        return (int(match.group("index")) if match else 10_000, stream_name)

    return sorted(streams, key=sort_key)


def _decompress_hwp_stream(data: bytes) -> bytes:
    try:
        return zlib.decompress(data, -15)
    except zlib.error:
        return zlib.decompress(data)


def _text_items_from_records(data: bytes) -> list[str]:
    items: list[str] = []
    offset = 0
    while offset + 4 <= len(data):
        header = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        tag = header & 0x3FF
        size = (header >> 20) & 0xFFF
        if size == EXTENDED_RECORD_SIZE:
            if offset + 4 > len(data):
                break
            size = struct.unpack_from("<I", data, offset)[0]
            offset += 4
        if size < 0 or offset + size > len(data):
            break
        payload = data[offset : offset + size]
        offset += size
        if tag != HWPTAG_PARA_TEXT:
            continue
        item = _clean_text_item(payload.decode("utf-16le", errors="ignore"))
        if item:
            items.append(item)
    return items


def _preview_text_items(content: bytes) -> list[str]:
    text = content.decode("utf-16le", errors="ignore")
    text = _clean_text_item(text)
    if not text:
        return []
    return re.findall(r"<([^<>]{1,300})>", text)


def _expense_rows_from_text_items(
    items: list[str],
    *,
    fallback_department: str,
    fallback_year: int | None,
) -> list[ParsedExpenseRow]:
    rows: list[ParsedExpenseRow] = []
    index = 0
    while index < len(items):
        if not _is_row_start(items, index):
            index += 1
            continue
        next_index = index + 1
        while next_index < len(items) and not _is_row_start(items, next_index):
            next_index += 1
        parsed = _parse_row_chunk(
            items[index:next_index],
            fallback_department=fallback_department,
            fallback_year=fallback_year,
        )
        if parsed:
            rows.append(parsed)
        index = next_index
    return rows


def _is_row_start(items: list[str], index: int) -> bool:
    if index + 3 >= len(items):
        return False
    if not BARE_NUMBER_RE.fullmatch(items[index]):
        return False
    if _looks_like_header(items[index + 1]):
        return False
    if FULL_DATE_RE.fullmatch(items[index + 2]):
        return True
    return BARE_NUMBER_RE.fullmatch(items[index + 2]) is not None and (
        BARE_NUMBER_RE.fullmatch(items[index + 3]) is not None
    )


def _parse_row_chunk(
    chunk: list[str],
    *,
    fallback_department: str,
    fallback_year: int | None,
) -> ParsedExpenseRow | None:
    if len(chunk) < 6:
        return None
    user_text = chunk[1]
    if FULL_DATE_RE.fullmatch(chunk[2]):
        date_text = chunk[2]
        values = chunk[3:]
    else:
        if fallback_year is None:
            return None
        try:
            month = int(chunk[2])
            day = int(chunk[3])
            date_text = date(fallback_year, month, day).isoformat()
        except ValueError:
            return None
        values = chunk[4:]

    amount_index = _find_amount_index(values)
    if amount_index is None:
        return None

    place_text, purpose = _split_place_and_purpose(values[:amount_index])
    amount = values[amount_index]
    party_size, payment_method, expense_category, time_text = _parse_tail_fields(
        values[amount_index + 1 :]
    )

    return build_expense_row(
        RawExpenseFields(
            department_name=fallback_department,
            date_text=date_text,
            time_text=time_text,
            place_text=place_text,
            purpose=purpose,
            amount=amount,
            party_size=party_size,
            user_text=user_text,
            payment_method=payment_method,
            expense_category=expense_category,
            raw_values=chunk,
        ),
        fallback_department=fallback_department,
    )


def _find_amount_index(values: list[str]) -> int | None:
    for index, value in enumerate(values):
        if index < 2:
            continue
        if not AMOUNT_RE.fullmatch(value.replace(" ", "")):
            continue
        trailing = values[index + 1 :]
        if not trailing or any(PAYMENT_RE.search(item) for item in trailing):
            return index
    return None


def _split_place_and_purpose(values: list[str]) -> tuple[str | None, str | None]:
    cleaned = [value for value in (_clean_text_item(item) for item in values) if value]
    if not cleaned:
        return None, None
    if len(cleaned) == 1:
        return cleaned[0], None

    purpose_index = next(
        (
            index
            for index, value in enumerate(cleaned[1:], start=1)
            if PURPOSE_START_RE.search(value)
        ),
        len(cleaned) - 1,
    )
    place_parts = cleaned[:purpose_index]
    purpose_parts = cleaned[purpose_index:]
    return " ".join(place_parts), " ".join(purpose_parts) or None


def _parse_tail_fields(values: list[str]) -> tuple[str | None, str | None, str | None, str | None]:
    payment_index = next(
        (index for index, value in enumerate(values) if PAYMENT_RE.search(value)),
        None,
    )
    if payment_index is None:
        time_text = next((value for value in values if TIME_RE.fullmatch(value)), None)
        return None, None, None, time_text

    party_size = " ".join(values[:payment_index]).strip() or None
    payment_method = values[payment_index]
    remainder = values[payment_index + 1 :]
    expense_category = next(
        (value for value in remainder if CATEGORY_RE.search(value)),
        None,
    )
    time_text = next((value for value in remainder if TIME_RE.fullmatch(value)), None)
    return party_size, payment_method, expense_category, time_text


def _document_year_month(
    items: list[str],
    source_title: str | None,
) -> tuple[int | None, int | None]:
    candidates = [source_title or "", *items[:20]]
    for candidate in candidates:
        match = TITLE_MONTH_RE.search(candidate)
        if not match:
            continue
        if match.group("year"):
            return int(match.group("year")), int(match.group("month"))
        return 2000 + int(match.group("short_year")), int(match.group("short_month"))
    return None, None


def _deduplicate_rows(rows: list[ParsedExpenseRow]) -> list[ParsedExpenseRow]:
    seen: set[tuple[object, ...]] = set()
    unique_rows: list[ParsedExpenseRow] = []
    for row in rows:
        key = (
            row.department_name,
            row.used_at,
            row.place_text,
            row.purpose,
            row.amount,
            row.payment_method,
        )
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(row)
    return unique_rows


def _looks_like_header(value: str) -> bool:
    return any(marker in value for marker in ("사용자", "사용일자", "사용장소", "연번", "금액"))


def _clean_text_item(value: str) -> str:
    text = "".join(
        " " if unicodedata.category(char).startswith("C") else char
        for char in value
    )
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _convert_hwp_to_html(content: bytes) -> bytes:
    soffice = shutil.which("soffice")
    if not soffice:
        raise PipelineConfigError(
            "HWP extraction requires LibreOffice CLI (`soffice`) or parseable HWP text records"
        )

    with tempfile.TemporaryDirectory(prefix="public-officer-hwp-") as tmp:
        tmp_path = Path(tmp)
        input_path = tmp_path / "input.hwp"
        input_path.write_bytes(content)
        command = [
            soffice,
            "--headless",
            "--convert-to",
            "html",
            "--outdir",
            str(tmp_path),
            str(input_path),
        ]
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                timeout=guards.PDF_SUBPROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise PipelineConfigError("LibreOffice HWP conversion timed out") from exc

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            stdout = result.stdout.decode("utf-8", errors="replace").strip()
            message = stderr or stdout or f"exit code {result.returncode}"
            raise PipelineConfigError(f"LibreOffice HWP conversion failed: {message}")

        output_candidates = sorted(
            path
            for path in tmp_path.iterdir()
            if path.suffix.lower() in {".html", ".htm"} and path.name != input_path.name
        )
        if not output_candidates:
            raise PipelineConfigError("LibreOffice HWP conversion produced no HTML output")

        output_path = output_candidates[0]
        guards.ensure_size_at_most(
            size=output_path.stat().st_size,
            max_bytes=guards.MAX_SPREADSHEET_BYTES,
            subject="converted HWP HTML",
        )
        return output_path.read_bytes()


__all__ = ["extract_hwp_rows"]
