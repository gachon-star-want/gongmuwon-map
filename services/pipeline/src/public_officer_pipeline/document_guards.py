from __future__ import annotations

from collections.abc import Mapping

from public_officer_pipeline.models import PipelineConfigError


MAX_DOCUMENT_DOWNLOAD_BYTES = 25 * 1024 * 1024
MAX_PDF_BYTES = 25 * 1024 * 1024
MAX_PDF_VISION_PAGES = 5
MIN_PDF_VISION_PAGES = 1
PDF_SUBPROCESS_TIMEOUT_SECONDS = 30.0
MAX_PDF_IMAGE_BYTES_PER_PAGE = 8 * 1024 * 1024
MAX_PDF_IMAGE_BYTES_TOTAL = 20 * 1024 * 1024
MAX_SPREADSHEET_BYTES = 25 * 1024 * 1024
MAX_SPREADSHEET_SHEETS = 20
MAX_SPREADSHEET_ROWS_PER_SHEET = 5_000
MAX_SPREADSHEET_COLUMNS_PER_SHEET = 100
MAX_SPREADSHEET_CELLS_TOTAL = 100_000


class DocumentProcessingLimitError(PipelineConfigError):
    pass


def ensure_size_at_most(*, size: int, max_bytes: int, subject: str) -> None:
    if size > max_bytes:
        raise DocumentProcessingLimitError(
            f"{subject} is {size} bytes, exceeding limit of {max_bytes} bytes"
        )


def content_length(headers: Mapping[str, str]) -> int | None:
    for name, value in headers.items():
        if name.lower() != "content-length":
            continue
        raw_value = value.split(",", 1)[0].strip()
        try:
            parsed = int(raw_value)
        except ValueError:
            return None
        return parsed if parsed >= 0 else None
    return None


def ensure_content_length_at_most(
    headers: Mapping[str, str],
    *,
    max_bytes: int,
    subject: str,
) -> None:
    length = content_length(headers)
    if length is None:
        return
    if length > max_bytes:
        raise DocumentProcessingLimitError(
            f"{subject} Content-Length is {length} bytes, exceeding limit of {max_bytes} bytes"
        )


def clamp_pdf_vision_pages(max_pages: int) -> int:
    try:
        requested = int(max_pages)
    except (TypeError, ValueError):
        requested = MIN_PDF_VISION_PAGES
    return min(max(requested, MIN_PDF_VISION_PAGES), MAX_PDF_VISION_PAGES)
