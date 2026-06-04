from __future__ import annotations

import zipfile
from io import BytesIO

from public_officer_pipeline import document_guards as guards
from public_officer_pipeline.extractor.hwp import extract_hwp_rows
from public_officer_pipeline.extractor.hwpx import extract_hwpx_rows
from public_officer_pipeline.extractor.pdf_vision import extract_pdf_rows_with_vision
from public_officer_pipeline.extractor.spreadsheet import extract_spreadsheet_rows
from public_officer_pipeline.models import ParsedExpenseRow, PipelineConfigError
from public_officer_pipeline.crawler.file_kind import detect_file_kind


SUPPORTED_ARCHIVE_KINDS = ("xlsx", "xls", "hwpx", "hwp", "pdf")


def extract_zip_rows(
    content: bytes,
    *,
    fallback_department: str,
    source_title: str,
) -> list[ParsedExpenseRow]:
    guards.ensure_size_at_most(
        size=len(content),
        max_bytes=guards.MAX_DOCUMENT_DOWNLOAD_BYTES,
        subject="ZIP document",
    )
    guards.preflight_xlsx_zip(content)

    rows: list[ParsedExpenseRow] = []
    first_error: PipelineConfigError | None = None
    with zipfile.ZipFile(BytesIO(content)) as archive:
        for member in sorted(
            archive.infolist(),
            key=lambda item: (_archive_kind_priority(detect_file_kind(item.filename)), item.filename),
        ):
            if member.is_dir():
                continue
            file_kind = detect_file_kind(member.filename)
            if file_kind not in SUPPORTED_ARCHIVE_KINDS:
                continue
            guards.ensure_size_at_most(
                size=member.file_size,
                max_bytes=guards.MAX_DOCUMENT_DOWNLOAD_BYTES,
                subject=f"ZIP member {member.filename!r}",
            )
            member_bytes = archive.read(member)
            department = _department_from_archive_name(member.filename) or fallback_department
            try:
                rows.extend(
                    _extract_member_rows(
                        member_bytes,
                        file_kind=file_kind,
                        fallback_department=department,
                        source_title=f"{source_title} - {member.filename}",
                    )
                )
            except PipelineConfigError as exc:
                if first_error is None:
                    first_error = exc
                continue

    if rows or first_error is None:
        return rows
    raise first_error


def _extract_member_rows(
    content: bytes,
    *,
    file_kind: str,
    fallback_department: str,
    source_title: str,
) -> list[ParsedExpenseRow]:
    if file_kind in {"xls", "xlsx"}:
        return extract_spreadsheet_rows(content, fallback_department=fallback_department)
    if file_kind == "hwpx":
        return extract_hwpx_rows(content, fallback_department=fallback_department)
    if file_kind == "hwp":
        return extract_hwp_rows(content, fallback_department=fallback_department)
    if file_kind == "pdf":
        return extract_pdf_rows_with_vision(
            content,
            fallback_department=fallback_department,
            source_title=source_title,
        )
    return []



def _archive_kind_priority(file_kind: str) -> int:
    return {
        "xlsx": 0,
        "xls": 1,
        "hwpx": 2,
        "hwp": 3,
        "pdf": 4,
    }.get(file_kind, 9)


def _department_from_archive_name(filename: str) -> str:
    stem = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    if "(" in stem and ")" in stem:
        inside = stem.rsplit("(", 1)[-1].split(")", 1)[0].strip()
        if inside:
            return inside
    return ""


__all__ = ["extract_zip_rows"]
