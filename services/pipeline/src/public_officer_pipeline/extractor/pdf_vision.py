from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import tempfile
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import httpx
from dateutil import parser as date_parser

from public_officer_pipeline.models import ParsedExpenseRow, PipelineConfigError
from public_officer_pipeline.normalizer.llm import _loads_json_response


SYSTEM_PROMPT = """Extract Korean public expense table rows from scanned PDF page images.

Return valid JSON only:
{"rows":[{"department_name":"...","used_at":"YYYY-MM-DDTHH:MM:SS","place_text":"상호명(주소)","purpose":"...","amount":12345,"user_text":"구의원 N명","payment_method":"카드"}]}

Rules:
- Extract every visible expense row.
- Use ISO dates. If a date has a 2-digit year like 26.1.5, convert it to 2026-01-05.
- If a row omits the date, inherit the most recent date above it.
- Put merchant and address together as "상호명(주소)" when an address is visible.
- For council chair, vice-chair, committee chair, or negotiation group representative roles, set user_text to "구의원 N명" using target headcount.
- Do not output personal names.
- Omit total/subtotal/header/footer rows.
- Do not include raw_excerpt unless explicitly necessary.
"""

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
PDF_TEXT_PURPOSE_STARTERS = (
    "의정활동",
    "직무수행",
    "의장 직무",
    "부의장 직무",
    "의회운영위원장",
    "기획행정위원장",
    "복지건설위원장",
    "의회사무국",
    "의정현안",
    "기획행정위원회",
    "복지건설위원회",
    "입법지원",
    "언론사",
)


def extract_pdf_rows_with_vision(
    content: bytes,
    *,
    fallback_department: str,
    source_title: str,
    max_pages: int = 2,
    anthropic_api_key: str | None = None,
    gemini_api_key: str | None = None,
    model: str | None = None,
) -> list[ParsedExpenseRow]:
    api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
    gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
    provider = os.getenv("PDF_VISION_PROVIDER", "gemini" if gemini_key else "anthropic")
    if provider == "anthropic" and not api_key:
        raise PipelineConfigError("ANTHROPIC_API_KEY is required for scanned PDF vision extraction")
    if provider == "gemini" and not gemini_key:
        raise PipelineConfigError("GEMINI_API_KEY is required for scanned PDF vision extraction")
    text = _pdf_to_text(content)
    if text:
        text_rows = rows_from_pdf_text(text, fallback_department=fallback_department)
        if text_rows or "총 0건" in text:
            return text_rows
    images = _pdf_to_png_images(content, max_pages=max_pages)
    rows: list[ParsedExpenseRow] = []
    for index, image in enumerate(images, start=1):
        if provider == "gemini":
            rows.extend(
                _extract_page_with_gemini(
                    image,
                    page_number=index,
                    fallback_department=fallback_department,
                    source_title=source_title,
                    api_key=gemini_key or "",
                    model=model or os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash"),
                )
            )
        else:
            rows.extend(
                _extract_page_with_anthropic(
                    image,
                    page_number=index,
                    fallback_department=fallback_department,
                    source_title=source_title,
                    api_key=api_key or "",
                    model=model
                    or os.getenv("ANTHROPIC_VISION_MODEL", os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")),
                )
            )
    return rows


def _pdf_to_png_images(content: bytes, *, max_pages: int) -> list[bytes]:
    with tempfile.TemporaryDirectory() as directory:
        pdf_path = Path(directory) / "source.pdf"
        output_prefix = Path(directory) / "page"
        pdf_path.write_bytes(content)
        command = [
            "pdftoppm",
            "-png",
            "-r",
            "180",
            "-f",
            "1",
            "-l",
            str(max_pages),
            str(pdf_path),
            str(output_prefix),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise PipelineConfigError("pdftoppm is required for scanned PDF vision extraction") from exc
        return [path.read_bytes() for path in sorted(Path(directory).glob("page-*.png"))]


def _pdf_to_text(content: bytes) -> str:
    with tempfile.TemporaryDirectory() as directory:
        pdf_path = Path(directory) / "source.pdf"
        pdf_path.write_bytes(content)
        command = ["pdftotext", "-layout", str(pdf_path), "-"]
        try:
            completed = subprocess.run(command, check=True, capture_output=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            return ""
        return completed.stdout.decode("utf-8", errors="ignore")


def _extract_page_with_anthropic(
    image: bytes,
    *,
    page_number: int,
    fallback_department: str,
    source_title: str,
    api_key: str,
    model: str,
) -> list[ParsedExpenseRow]:
    payload = {
        "source_title": source_title,
        "page_number": page_number,
        "fallback_department": fallback_department,
    }
    response = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 8192,
            "temperature": 0,
            "system": SYSTEM_PROMPT,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64.b64encode(image).decode("ascii"),
                            },
                        },
                        {
                            "type": "text",
                            "text": "Extract this scanned public expense table. Context:\n"
                            + json.dumps(payload, ensure_ascii=False),
                        },
                    ],
                }
            ],
        },
        timeout=90.0,
    )
    response.raise_for_status()
    body = response.json()
    text = "".join(block.get("text", "") for block in body.get("content", []) if block.get("type") == "text")
    try:
        parsed = _loads_json_response(text)
    except JSONDecodeError as exc:
        raise PipelineConfigError(f"Vision extraction returned invalid JSON: {exc}") from exc
    return rows_from_vision_payload(parsed, fallback_department=fallback_department)


def _extract_page_with_gemini(
    image: bytes,
    *,
    page_number: int,
    fallback_department: str,
    source_title: str,
    api_key: str,
    model: str,
) -> list[ParsedExpenseRow]:
    payload = {
        "source_title": source_title,
        "page_number": page_number,
        "fallback_department": fallback_department,
    }
    last_json_error: JSONDecodeError | None = None
    for attempt in range(2):
        extra_instruction = ""
        if attempt:
            extra_instruction = "\nReturn one complete JSON object. Do not omit commas between rows or fields."
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": api_key},
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": (
                                    f"{SYSTEM_PROMPT}{extra_instruction}\n\n"
                                    f"Context:\n{json.dumps(payload, ensure_ascii=False)}"
                                )
                            },
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": base64.b64encode(image).decode("ascii"),
                                }
                            },
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0,
                    "maxOutputTokens": 16384,
                    "responseMimeType": "application/json",
                },
            },
            timeout=90.0,
        )
        response.raise_for_status()
        body = response.json()
        parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts)
        try:
            parsed = _loads_json_response(text)
            return rows_from_vision_payload(parsed, fallback_department=fallback_department)
        except JSONDecodeError as exc:
            last_json_error = exc
    raise PipelineConfigError(f"Vision extraction returned invalid JSON: {last_json_error}") from last_json_error


def rows_from_vision_payload(payload: dict[str, Any], *, fallback_department: str) -> list[ParsedExpenseRow]:
    rows: list[ParsedExpenseRow] = []
    for item in payload.get("rows", []):
        parsed = _parse_vision_row(item, fallback_department=fallback_department)
        if parsed:
            rows.append(parsed)
    return rows


def rows_from_pdf_text(text: str, *, fallback_department: str) -> list[ParsedExpenseRow]:
    rows: list[ParsedExpenseRow] = []
    for line in text.splitlines():
        parsed = _parse_pdf_text_line(line, fallback_department=fallback_department)
        if parsed:
            rows.append(parsed)
    return rows


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
    user_amount_purpose = _parse_pdf_text_user_amount_purpose_line(line, fallback_department=fallback_department)
    if user_amount_purpose:
        return user_amount_purpose
    user_no_address = _parse_pdf_text_user_no_address_line(line, fallback_department=fallback_department)
    if user_no_address:
        return user_no_address
    purpose_first = _parse_pdf_text_purpose_first_line(line, fallback_department=fallback_department)
    if purpose_first:
        return purpose_first
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
    try:
        used_at = date_parser.parse(f"{row_match.group('date')} {row_match.group('time')}", fuzzy=True)
        amount = int(str(amount_match.group("amount")).replace(",", ""))
    except (TypeError, ValueError):
        return None
    party_size = amount_match.group("party_size")
    user_text_parts = [part for part in (row_match.group("user"), f"{party_size}명" if party_size else None) if part]
    raw_excerpt = " | ".join(
        part
        for part in (
            row_match.group("date"),
            row_match.group("time"),
            place_text,
            purpose,
            amount_match.group("amount"),
            party_size,
            amount_match.group("payment_method"),
        )
        if part
    )
    return ParsedExpenseRow(
        department_name=fallback_department,
        used_at=used_at.replace(tzinfo=None),
        place_text=place_text,
        purpose=purpose,
        amount=amount,
        user_text=" ".join(user_text_parts) if user_text_parts else None,
        payment_method=amount_match.group("payment_method"),
        raw_excerpt=raw_excerpt,
    )


def _parse_pdf_text_user_address_line(line: str, *, fallback_department: str) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_USER_ADDRESS_ROW_RE.match(line)
    if not row_match:
        return None
    body_match = PDF_TEXT_PLACE_ADDRESS_PURPOSE_RE.match(row_match.group("body").strip())
    if not body_match:
        return None
    try:
        used_at = date_parser.parse(f"{row_match.group('date')} {row_match.group('time')}", fuzzy=True)
        amount = int(str(row_match.group("amount")).replace(",", ""))
    except (TypeError, ValueError):
        return None
    party_size = row_match.group("party_size")
    user_text = "구의원"
    if party_size and party_size != "-":
        user_text = f"{user_text} {party_size}명"
    place = body_match.group("place").strip()
    address = body_match.group("address").strip()
    purpose = body_match.group("purpose").strip()
    raw_excerpt = " | ".join(
        part
        for part in (
            row_match.group("user"),
            row_match.group("date"),
            row_match.group("time"),
            place,
            address,
            purpose,
            None if party_size == "-" else party_size,
            row_match.group("amount"),
            row_match.group("payment_method"),
            row_match.group("expense_category"),
        )
        if part
    )
    return ParsedExpenseRow(
        department_name=fallback_department,
        used_at=used_at.replace(tzinfo=None),
        place_text=f"{place}({address})",
        purpose=purpose,
        amount=amount,
        user_text=user_text,
        payment_method=row_match.group("payment_method"),
        expense_category=row_match.group("expense_category"),
        raw_excerpt=raw_excerpt,
    )


def _parse_pdf_text_date_user_amount_place_line(line: str, *, fallback_department: str) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_DATE_USER_AMOUNT_PLACE_ROW_RE.match(line)
    if not row_match:
        return None
    place, purpose = _split_place_and_purpose(row_match.group("body").strip(), row_match.group("user").strip())
    if not place or not purpose:
        return None
    try:
        used_at = date_parser.parse(f"{row_match.group('date')} {row_match.group('time')}", fuzzy=True)
        amount = int(str(row_match.group("amount")).replace(",", ""))
    except (TypeError, ValueError):
        return None
    party_size = row_match.group("party_size")
    user_text = row_match.group("user").strip()
    if party_size and party_size != "-":
        user_text = f"{user_text} {party_size}명"
    raw_excerpt = " | ".join(
        part
        for part in (
            row_match.group("date"),
            row_match.group("time"),
            row_match.group("user"),
            row_match.group("amount"),
            place,
            purpose,
            None if party_size == "-" else party_size,
            row_match.group("payment_method"),
            row_match.group("expense_category"),
        )
        if part
    )
    return ParsedExpenseRow(
        department_name=fallback_department,
        used_at=used_at.replace(tzinfo=None),
        place_text=place,
        purpose=purpose,
        amount=amount,
        user_text=user_text,
        payment_method=row_match.group("payment_method"),
        expense_category=row_match.group("expense_category"),
        raw_excerpt=raw_excerpt,
    )


def _parse_pdf_text_user_amount_purpose_line(line: str, *, fallback_department: str) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_USER_AMOUNT_PURPOSE_ROW_RE.match(line)
    if not row_match:
        return None
    try:
        used_at = date_parser.parse(f"{row_match.group('date')} {row_match.group('time')}", fuzzy=True)
        amount = int(str(row_match.group("amount")).replace(",", ""))
    except (TypeError, ValueError):
        return None
    party_size = row_match.group("party_size")
    user_text = row_match.group("user").strip()
    if party_size and party_size != "-":
        user_text = f"{user_text} {party_size}명"
    raw_excerpt = " | ".join(
        part
        for part in (
            row_match.group("user"),
            row_match.group("date"),
            row_match.group("time"),
            row_match.group("place"),
            row_match.group("amount"),
            row_match.group("purpose"),
            None if party_size == "-" else party_size,
            row_match.group("payment_method"),
            row_match.group("expense_category"),
        )
        if part
    )
    return ParsedExpenseRow(
        department_name=fallback_department,
        used_at=used_at.replace(tzinfo=None),
        place_text=row_match.group("place").strip(),
        purpose=row_match.group("purpose").strip(),
        amount=amount,
        user_text=user_text,
        payment_method=row_match.group("payment_method"),
        expense_category=row_match.group("expense_category"),
        raw_excerpt=raw_excerpt,
    )


def _parse_pdf_text_user_no_address_line(line: str, *, fallback_department: str) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_USER_NO_ADDRESS_ROW_RE.match(line)
    if not row_match:
        return None
    place, purpose = _split_place_and_purpose(row_match.group("body").strip(), row_match.group("user").strip())
    if not place or not purpose:
        return None
    try:
        used_at = date_parser.parse(f"{row_match.group('date')} {row_match.group('time')}", fuzzy=True)
        amount = int(str(row_match.group("amount")).replace(",", ""))
    except (TypeError, ValueError):
        return None
    party_size = re.sub(r"\D", "", row_match.group("party_size"))
    user_text = "구의원"
    if party_size:
        user_text = f"{user_text} {party_size}명"
    raw_excerpt = " | ".join(
        part
        for part in (
            row_match.group("user"),
            row_match.group("date"),
            row_match.group("time"),
            place,
            purpose,
            row_match.group("party_size"),
            row_match.group("amount"),
            row_match.group("payment_method"),
            row_match.group("expense_category"),
        )
        if part
    )
    return ParsedExpenseRow(
        department_name=fallback_department,
        used_at=used_at.replace(tzinfo=None),
        place_text=place,
        purpose=purpose,
        amount=amount,
        user_text=user_text,
        payment_method=row_match.group("payment_method"),
        expense_category=row_match.group("expense_category"),
        raw_excerpt=raw_excerpt,
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


def _parse_pdf_text_purpose_first_line(line: str, *, fallback_department: str) -> ParsedExpenseRow | None:
    row_match = PDF_TEXT_PURPOSE_FIRST_ROW_RE.match(line)
    if not row_match:
        return None
    try:
        used_at = date_parser.parse(f"{row_match.group('date')} {row_match.group('time')}", fuzzy=True)
        amount = int(str(row_match.group("amount")).replace(",", ""))
    except (TypeError, ValueError):
        return None
    party_size = row_match.group("party_size")
    user_text_parts = [fallback_department]
    if party_size and party_size != "-":
        user_text_parts.append(f"{party_size}명")
    raw_excerpt = " | ".join(
        part
        for part in (
            row_match.group("date"),
            row_match.group("time"),
            row_match.group("place_text"),
            row_match.group("purpose"),
            row_match.group("amount"),
            None if party_size == "-" else party_size,
            row_match.group("payment_method"),
        )
        if part
    )
    return ParsedExpenseRow(
        department_name=fallback_department,
        used_at=used_at.replace(tzinfo=None),
        place_text=row_match.group("place_text").strip(),
        purpose=row_match.group("purpose").strip(),
        amount=amount,
        user_text=" ".join(user_text_parts),
        payment_method=row_match.group("payment_method"),
        raw_excerpt=raw_excerpt,
    )


def _parse_vision_row(item: dict[str, Any], *, fallback_department: str) -> ParsedExpenseRow | None:
    if not item.get("used_at") or not item.get("place_text") or not item.get("amount"):
        return None
    try:
        used_at = date_parser.parse(str(item["used_at"]), fuzzy=True)
        amount = int(re.sub(r"[^\d]", "", str(item["amount"])))
    except (TypeError, ValueError):
        return None
    if amount <= 0:
        return None

    raw_excerpt = item.get("raw_excerpt") or " | ".join(
        str(item.get(key) or "")
        for key in ("used_at", "place_text", "purpose", "amount", "payment_method")
        if item.get(key)
    )
    return ParsedExpenseRow(
        department_name=str(item.get("department_name") or fallback_department).strip(),
        used_at=used_at.replace(tzinfo=None),
        place_text=str(item["place_text"]).strip(),
        purpose=str(item["purpose"]).strip() if item.get("purpose") else None,
        amount=amount,
        user_text=str(item["user_text"]).strip() if item.get("user_text") else None,
        payment_method=str(item["payment_method"]).strip() if item.get("payment_method") else None,
        expense_category=str(item["expense_category"]).strip() if item.get("expense_category") else None,
        raw_excerpt=raw_excerpt,
    )
