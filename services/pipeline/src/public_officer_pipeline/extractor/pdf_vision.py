from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from public_officer_pipeline import document_guards as guards
from public_officer_pipeline.extractor.pdf_text import text_parser as pdf_text_parser
from public_officer_pipeline.llm import LLMClient, TaskType
from public_officer_pipeline.models import ParsedExpenseRow, PipelineConfigError


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

# Compatibility re-exports for older callers/tests that still import parser
# internals from this module.
rows_from_pdf_text = pdf_text_parser.rows_from_pdf_text
_parse_pdf_text_line = pdf_text_parser._parse_pdf_text_line
_parse_pdf_text_generic_row = pdf_text_parser._parse_pdf_text_generic_row
_parse_pdf_text_user_address_line = pdf_text_parser._parse_pdf_text_user_address_line
_parse_pdf_text_date_user_amount_place_line = pdf_text_parser._parse_pdf_text_date_user_amount_place_line
_parse_pdf_text_purpose_place_amount_line = pdf_text_parser._parse_pdf_text_purpose_place_amount_line
_parse_pdf_text_region_amount_place_purpose_line = pdf_text_parser._parse_pdf_text_region_amount_place_purpose_line
_parse_pdf_text_optional_user_place_purpose_amount_line = (
    pdf_text_parser._parse_pdf_text_optional_user_place_purpose_amount_line
)
_parse_pdf_text_user_amount_place_address_purpose_line = (
    pdf_text_parser._parse_pdf_text_user_amount_place_address_purpose_line
)
_parse_pdf_text_user_place_purpose_amount_line = pdf_text_parser._parse_pdf_text_user_place_purpose_amount_line
_parse_pdf_text_user_amount_purpose_line = pdf_text_parser._parse_pdf_text_user_amount_purpose_line
_parse_pdf_text_user_no_address_line = pdf_text_parser._parse_pdf_text_user_no_address_line
_parse_pdf_text_purpose_first_line = pdf_text_parser._parse_pdf_text_purpose_first_line
_parse_user_place_purpose_layout_pdf_text = pdf_text_parser._parse_user_place_purpose_layout_pdf_text
_parse_layout_office_pdf_text = pdf_text_parser._parse_layout_office_pdf_text
_parse_segmented_office_pdf_text = pdf_text_parser._parse_segmented_office_pdf_text
_build_pdf_row = pdf_text_parser._build_pdf_row


async def _extract_pdf_rows_with_vision(
    content: bytes,
    *,
    fallback_department: str,
    source_title: str,
    max_pages: int = 2,
    anthropic_api_key: str | None = None,
    gemini_api_key: str | None = None,
    model: str | None = None,
) -> list[ParsedExpenseRow]:
    anthropic_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
    gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
    text = _pdf_to_text(content)
    if text:
        text_rows = rows_from_pdf_text(text, fallback_department=fallback_department)
        if text_rows or "총 0건" in text:
            return text_rows
    plain_text = _pdf_to_text(content, layout=False)
    if plain_text and plain_text != text:
        plain_text_rows = rows_from_pdf_text(plain_text, fallback_department=fallback_department)
        if plain_text_rows or "총 0건" in plain_text:
            return plain_text_rows
    if _expense_text_is_aggregate_only(text) or _expense_text_is_aggregate_only(plain_text):
        return []
    if _expense_text_lacks_place_column(text) or _expense_text_lacks_place_column(plain_text):
        return []
    if not anthropic_key and not gemini_key and not os.getenv("OPENAI_API_KEY"):
        raise PipelineConfigError("At least one LLM API key is required for scanned PDF vision extraction")

    client = LLMClient(
        anthropic_api_key=anthropic_key,
        gemini_api_key=gemini_key,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model_by_provider=(
            {"anthropic": {TaskType.PDF_VISION_EXTRACT: model}} if model is not None else None
        ),
    )

    images = _pdf_to_png_images(content, max_pages=max_pages)
    rows: list[ParsedExpenseRow] = []
    for index, image in enumerate(images, start=1):
        rows.extend(
            await _extract_page_with_vision(
                client,
                image,
                page_number=index,
                fallback_department=fallback_department,
                source_title=source_title,
            )
        )
    return rows


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
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            _extract_pdf_rows_with_vision(
                content,
                fallback_department=fallback_department,
                source_title=source_title,
                max_pages=max_pages,
                anthropic_api_key=anthropic_api_key,
                gemini_api_key=gemini_api_key,
                model=model,
            )
        )

    result: dict[str, object] = {}
    error: dict[str, BaseException] = {}

    def _run() -> None:
        try:
            result["rows"] = asyncio.run(
                _extract_pdf_rows_with_vision(
                    content,
                    fallback_department=fallback_department,
                    source_title=source_title,
                    max_pages=max_pages,
                    anthropic_api_key=anthropic_api_key,
                    gemini_api_key=gemini_api_key,
                    model=model,
                )
            )
        except BaseException as exc:  # pragma: no cover - defensive
            error["exception"] = exc

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join()
    if "exception" in error:
        raise error["exception"]
    return result["rows"]  # type: ignore[return-value]


def _pdf_to_png_images(content: bytes, *, max_pages: int) -> list[bytes]:
    guards.ensure_size_at_most(
        size=len(content),
        max_bytes=guards.MAX_PDF_BYTES,
        subject="PDF document",
    )
    page_limit = guards.clamp_pdf_vision_pages(max_pages)
    with tempfile.TemporaryDirectory() as directory:
        pdf_path = Path(directory) / "source.pdf"
        output_prefix = Path(directory) / "page"
        pdf_path.write_bytes(content)
        command = [
            "pdftoppm",
            "-png",
            "-r",
            str(guards.PDF_VISION_RENDER_DPI),
            "-f",
            "1",
            "-l",
            str(page_limit),
            str(pdf_path),
            str(output_prefix),
        ]
        try:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=guards.PDF_SUBPROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise PipelineConfigError(
                f"pdftoppm timed out after {guards.PDF_SUBPROCESS_TIMEOUT_SECONDS:g} seconds"
            ) from exc
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise PipelineConfigError("pdftoppm is required for scanned PDF vision extraction") from exc
        paths = sorted(Path(directory).glob("page-*.png"))
        if len(paths) > page_limit:
            raise guards.DocumentProcessingLimitError(
                f"pdftoppm generated {len(paths)} images, exceeding limit of {page_limit}"
            )
        images: list[bytes] = []
        total_size = 0
        for path in paths:
            image_size = path.stat().st_size
            guards.ensure_size_at_most(
                size=image_size,
                max_bytes=guards.MAX_PDF_IMAGE_BYTES_PER_PAGE,
                subject=f"generated PDF image {path.name}",
            )
            total_size += image_size
            guards.ensure_size_at_most(
                size=total_size,
                max_bytes=guards.MAX_PDF_IMAGE_BYTES_TOTAL,
                subject="generated PDF images",
            )
            images.append(path.read_bytes())
        return images


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    try:
        process.kill()
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        return


def _run_subprocess_with_output_file_limit(
    command: list[str],
    *,
    output_path: Path,
    max_bytes: int,
    subject: str,
    timeout_seconds: float,
) -> None:
    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + timeout_seconds
    try:
        while True:
            if output_path.exists():
                guards.ensure_size_at_most(
                    size=output_path.stat().st_size,
                    max_bytes=max_bytes,
                    subject=subject,
                )
            returncode = process.poll()
            if returncode is not None:
                if output_path.exists():
                    guards.ensure_size_at_most(
                        size=output_path.stat().st_size,
                        max_bytes=max_bytes,
                        subject=subject,
                    )
                if returncode != 0:
                    raise subprocess.CalledProcessError(returncode, command)
                return
            if time.monotonic() >= deadline:
                _terminate_process(process)
                raise subprocess.TimeoutExpired(command, timeout_seconds)
            time.sleep(0.05)
    except guards.DocumentProcessingLimitError:
        _terminate_process(process)
        raise


def _pdf_to_text(content: bytes, *, layout: bool = True) -> str:
    guards.ensure_size_at_most(
        size=len(content),
        max_bytes=guards.MAX_PDF_BYTES,
        subject="PDF document",
    )
    with tempfile.TemporaryDirectory() as directory:
        pdf_path = Path(directory) / "source.pdf"
        text_path = Path(directory) / "output.txt"
        pdf_path.write_bytes(content)
        command = ["pdftotext", *(["-layout"] if layout else []), str(pdf_path), str(text_path)]
        try:
            _run_subprocess_with_output_file_limit(
                command,
                output_path=text_path,
                max_bytes=guards.MAX_PDF_TEXT_BYTES,
                subject="extracted PDF text",
                timeout_seconds=guards.PDF_SUBPROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise PipelineConfigError(
                f"pdftotext timed out after {guards.PDF_SUBPROCESS_TIMEOUT_SECONDS:g} seconds"
            ) from exc
        except (FileNotFoundError, subprocess.CalledProcessError):
            return ""
        if not text_path.exists():
            return ""
        return text_path.read_bytes().decode("utf-8", errors="ignore")


def _expense_text_lacks_place_column(text: str) -> bool:
    if not text:
        return False
    compact = re.sub(r"\s+", "", text)
    has_expense_columns = "집행목적" in compact and ("집행금액" in compact or "사용금액" in compact)
    has_place_column = any(
        keyword in compact for keyword in ("집행장소", "사용장소", "가맹점", "상호", "집행처", "장소")
    )
    return has_expense_columns and not has_place_column


def _expense_text_is_aggregate_only(text: str) -> bool:
    if not text:
        return False
    compact = re.sub(r"\s+", "", text)
    has_place_column = any(
        keyword in compact for keyword in ("집행장소", "사용장소", "가맹점", "상호", "집행처", "장소")
    )
    if has_place_column:
        return False
    has_amount = "금액" in compact or "집행액" in compact or "사용액" in compact
    has_aggregate_axis = any(
        keyword in compact
        for keyword in (
            "월별",
            "구분별",
            "유형별",
            "분기별",
            "건수",
            "합계",
            "총계",
            "집행내역",
        )
    )
    has_workcost_context = "업무추진비" in compact or "기관장" in compact or "이사장" in compact
    return has_workcost_context and has_amount and has_aggregate_axis


async def _extract_page_with_vision(
    client: LLMClient,
    image: bytes,
    *,
    page_number: int,
    fallback_department: str,
    source_title: str,
) -> list[ParsedExpenseRow]:
    del page_number
    guards.ensure_size_at_most(
        size=len(image),
        max_bytes=guards.MAX_PDF_IMAGE_BYTES_PER_PAGE,
        subject="generated PDF image",
    )
    payload = {
        "source_title": source_title,
        "fallback_department": fallback_department,
    }
    prompt = json.dumps(
        {
            "system_prompt": SYSTEM_PROMPT,
            "user_prompt": "Extract this scanned public expense table. Context:\n"
            + json.dumps(payload, ensure_ascii=False),
            "image_base64": base64.b64encode(image).decode("ascii"),
        },
        ensure_ascii=False,
    )
    result = await client.extract(
        task=TaskType.PDF_VISION_EXTRACT,
        prompt=prompt,
        schema={"required": ["rows"]},
        timeout=90.0,
    )
    return rows_from_vision_payload(result.payload, fallback_department=fallback_department)


def rows_from_vision_payload(payload: dict[str, Any], *, fallback_department: str) -> list[ParsedExpenseRow]:
    rows: list[ParsedExpenseRow] = []
    for item in payload.get("rows", []):
        parsed = _parse_vision_row(item, fallback_department=fallback_department)
        if parsed:
            rows.append(parsed)
    return rows


def _parse_vision_row(item: dict[str, Any], *, fallback_department: str) -> ParsedExpenseRow | None:
    return _build_pdf_row(
        {
            "department_name": str(item.get("department_name") or fallback_department).strip(),
            "used_at": item.get("used_at"),
            "place_text": str(item["place_text"]).strip() if item.get("place_text") else None,
            "purpose": str(item["purpose"]).strip() if item.get("purpose") else None,
            "amount": item.get("amount"),
            "user_text": str(item["user_text"]).strip() if item.get("user_text") else None,
            "payment_method": str(item["payment_method"]).strip() if item.get("payment_method") else None,
            "expense_category": str(item["expense_category"]).strip() if item.get("expense_category") else None,
            "party_size": None,
        },
        fallback_department=fallback_department,
        raw_values=[str(value) for value in filter(None, [item.get("raw_excerpt")])],
    )
