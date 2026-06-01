from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from public_officer_pipeline.models import Agency

ALLOWED_FILE_KINDS = ("pdf", "hwp", "hwpx", "xls", "xlsx", "html")
FileKind = Literal["pdf", "hwp", "hwpx", "xls", "xlsx", "html"]


class SourcePatternError(ValueError):
    """Raised when a source pattern payload cannot be parsed into a known pattern."""


class SourcePattern(BaseModel):
    adapter: str
    status: str | None = None


class SeoulOpenGovPattern(SourcePattern):
    adapter: Literal["seoul_opengov"]
    searchKeyword: str
    titleIncludes: list[str] = Field(default_factory=list)


class AttachmentBoardPattern(SourcePattern):
    adapter: Literal["attachment_board", "council_attachment_board", "gangnam_xlsx_board"]
    listUrl: str
    extraListUrls: list[str] = Field(default_factory=list)
    fileKinds: list[FileKind] = Field(default_factory=lambda: list(ALLOWED_FILE_KINDS))
    defaultFileKind: FileKind | None = None
    followDetail: bool = False
    pageParam: str = "page"
    pageUnitParam: str | None = None
    rowsPerPage: int = 10
    jsDownloadPath: str | None = None
    userAgent: str | None = None

    @field_validator("fileKinds", mode="before")
    @classmethod
    def _normalize_file_kinds(cls, value: Any) -> list[str]:
        if value is None:
            return list(ALLOWED_FILE_KINDS)
        if not isinstance(value, list):
            raise ValueError("fileKinds must be a list")
        normalized = [str(item).lower().strip() for item in value]
        if not normalized:
            raise ValueError("fileKinds must be a non-empty list")
        return normalized


class EstimateListPattern(SourcePattern):
    adapter: Literal["estimate_list_html"]
    listUrl: str = "https://www.gwanak.go.kr/site/gwanak/estimate/estimateList.do"
    rowsPerPage: int = 10


class InlineExpenseTablePattern(SourcePattern):
    adapter: Literal["inline_expense_table"]
    listUrl: str
    pageParam: str = "pageIndex"
    pageUnitParam: str = "pageUnit"
    rowsPerPage: int = 100


class AdapterRequiredPattern(SourcePattern):
    status: Literal["adapter_required"]


ParsedSourcePattern = (
    SeoulOpenGovPattern
    | AttachmentBoardPattern
    | EstimateListPattern
    | InlineExpenseTablePattern
    | AdapterRequiredPattern
)


def parse_source_pattern(agency: Agency) -> ParsedSourcePattern:
    raw = agency.source_pattern
    if not isinstance(raw, dict):
        raise SourcePatternError("source_pattern must be a mapping")

    status = raw.get("status")
    if status == "adapter_required":
        return AdapterRequiredPattern(**raw)

    adapter = raw.get("adapter")
    if not adapter:
        raise SourcePatternError("source_pattern.adapter is required")

    try:
        if adapter == "seoul_opengov":
            return SeoulOpenGovPattern(**raw)
        if adapter in {"attachment_board", "council_attachment_board", "gangnam_xlsx_board"}:
            return AttachmentBoardPattern(**raw)
        if adapter == "estimate_list_html":
            return EstimateListPattern(**raw)
        if adapter == "inline_expense_table":
            return InlineExpenseTablePattern(**raw)
    except ValidationError as exc:
        raise SourcePatternError(str(exc)) from exc

    raise SourcePatternError(f"unknown adapter: {adapter}")
