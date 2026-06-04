from __future__ import annotations

import re

SUPPORTED_FILE_KINDS = {"pdf", "hwp", "xls", "xlsx", "hwpx", "zip"}


def detect_file_kind(filename: str | None) -> str:
    lowered = (filename or "").lower()
    normalized = re.sub(r"\s+", " ", (filename or "").lower()).strip()
    if "excel" in normalized or "엑셀" in normalized:
        return "xlsx"
    if "hwpx" in normalized:
        return "hwpx"
    if "한글" in normalized or re.search(r"\bhwp\b|\.hwp(?:\b|[^\w])", normalized):
        return "hwp"
    for file_kind in SUPPORTED_FILE_KINDS:
        if (
            re.search(rf"\.{file_kind}(?:\b|[^\w])", lowered)
            or f"{file_kind}파일" in lowered
            or re.search(rf"\b{file_kind}\s*파일\b", lowered)
            or re.search(rf"\b{file_kind}\s*첨부파일\b", lowered)
        ):
            return file_kind
    return ""
