from __future__ import annotations

from enum import StrEnum
from json import JSONDecodeError
from typing import Any, Protocol
import json
import re

from pydantic import BaseModel


class TaskType(StrEnum):
    TABLE_NORMALIZE = "table_normalize"
    PDF_TEXT_EXTRACT = "pdf_text_extract"
    PDF_VISION_EXTRACT = "pdf_vision_extract"
    MASKING_VERIFY = "masking_verify"
    NAME_NORMALIZE = "name_normalize"
    SITE_ADAPTER_INFER = "site_adapter_infer"
    NEIGHBORHOOD_SUMMARY_POLISH = "neighborhood_summary_polish"


class ExtractResult(BaseModel):
    payload: dict[str, Any]
    provider: str
    model: str
    confidence: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    thinking_tokens: int | None = None


class LLMProvider(Protocol):
    name: str

    async def extract(
        self,
        *,
        task: TaskType,
        prompt: str,
        schema: dict[str, Any],
        timeout: float,
        reasoning: object | None = None,
    ) -> ExtractResult: ...


class LLMRetryableError(RuntimeError):
    """LLM failures that can move to the next provider."""


class LLMValidationError(LLMRetryableError):
    """Output is malformed, invalid, or low confidence."""


class LLMUnavailableError(RuntimeError):
    """Provider is not available due missing credentials or config."""


__all__ = [
    "TaskType",
    "ExtractResult",
    "LLMProvider",
    "LLMRetryableError",
    "LLMValidationError",
    "LLMUnavailableError",
    "_loads_json_response",
    "_repair_common_json_response",
]


def _loads_json_response(text: str) -> dict:
    stripped = text.strip()
    if not stripped:
        raise JSONDecodeError("empty response", text, 0)

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, flags=re.DOTALL)
    if fenced:
        stripped = fenced.group(1)
    else:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            stripped = stripped[start : end + 1]

    try:
        return json.loads(stripped)
    except JSONDecodeError:
        repaired = _repair_common_json_response(stripped)
        if repaired != stripped:
            return json.loads(repaired)
        raise


def _repair_common_json_response(value: str) -> str:
    repaired = value
    repaired = re.sub(r"}\s*\n(\s*){", r"},\n\1{", repaired)
    repaired = re.sub(r"}\s*{", "},{", repaired)
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    repaired = re.sub(r'(?<=[\]"0-9}])\s*\n\s*"', ',\n"', repaired)
    return repaired
