from __future__ import annotations

import json
import os
from datetime import date
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from public_officer_pipeline.agencies import Agency, SEOUL_AGENCIES
from public_officer_pipeline.legal.visibility import (
    LegalVisibilityError,
    allowed_elected_ranks_for_agency,
    sanitize_raw_excerpt,
)
from public_officer_pipeline.llm import LLMClient, TaskType
from public_officer_pipeline.llm.schema import _loads_json_response, _repair_common_json_response
from public_officer_pipeline.models import NormalizedVisit, ParsedExpenseRow, PipelineConfigError
from public_officer_pipeline.normalizer.rules import deterministic_normalize_rows

_SEOUL_AGENCY_IDS = {agency.id for agency in SEOUL_AGENCIES}

_APPOINTED_RANK_LABELS = (
    "부시장",
    "부지사",
    "부군수",
    "부구청장",
    "실장",
    "국장",
    "본부장",
    "과장",
    "팀장",
    "담당관",
    "전문위원",
    "주무관",
    "직원",
)

_CONFIDENCE_LABELS = {
    "high": 0.9,
    "medium": 0.7,
    "low": 0.4,
    "높음": 0.9,
    "중간": 0.7,
    "보통": 0.7,
    "낮음": 0.4,
}
_DEFAULT_LLM_CONFIDENCE = 0.8


def _system_prompt_for(agency: Agency) -> str:
    allowed_elected = ", ".join(allowed_elected_ranks_for_agency(agency))
    return f"""You normalize Korean public expense execution records into JSON.

Masking rules are mandatory:
1. Fill representative only for elected ranks: {allowed_elected}.
2. For appointed ranks such as {', '.join(_APPOINTED_RANK_LABELS)}, set representative to null.
3. For 5급 이하 or staff groups, set rank_label to \"5급 이하\" and keep only department-level labels.
4. Never output a private person's name except elected officials covered by rule 1.
5. Return valid JSON only, with a top-level visits array.
"""


class Normalizer:
    def __init__(
        self,
        *,
        anthropic_api_key: str | None = None,
        model: str | None = None,
        allow_deterministic_fallback: bool = False,
    ) -> None:
        self.allow_deterministic_fallback = allow_deterministic_fallback
        self.force_deterministic = os.getenv("FORCE_DETERMINISTIC_NORMALIZER", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        model_override = model or os.getenv("ANTHROPIC_MODEL")
        model_overrides: dict[str, dict[TaskType, str | None]] = {}
        if model_override is not None:
            model_overrides["anthropic"] = {TaskType.TABLE_NORMALIZE: model_override}

        self._llm_client = LLMClient(
            anthropic_api_key=anthropic_api_key,
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model_by_provider=model_overrides,
        )

    async def normalize_rows(
        self,
        *,
        agency_id: UUID,
        agency: Agency | None = None,
        source_url: str,
        source_title: str,
        source_published_at: date | None,
        source_hash_sha256: str,
        rows: list[ParsedExpenseRow],
    ) -> list[NormalizedVisit]:
        if not rows:
            return []
        if agency is None:
            if agency_id not in _SEOUL_AGENCY_IDS:
                raise PipelineConfigError(
                    "Non-Seoul agencies require explicit Agency context in normalize_rows; "
                    "pass agency from the caller before loading non-Seoul data."
                )
            agency = Agency()

        try:
            allowed_elected_ranks_for_agency(agency)
        except LegalVisibilityError as exc:
            raise PipelineConfigError(str(exc)) from exc

        if self.force_deterministic:
            return deterministic_normalize_rows(
                agency=agency,
                agency_id=agency_id,
                source_url=source_url,
                source_title=source_title,
                source_published_at=source_published_at,
                source_hash_sha256=source_hash_sha256,
                rows=rows,
            )

        try:
            return await self._normalize_with_llm(
                agency=agency,
                agency_id=agency_id,
                source_url=source_url,
                source_title=source_title,
                source_published_at=source_published_at,
                source_hash_sha256=source_hash_sha256,
                rows=rows,
            )
        except (PipelineConfigError, ValidationError, KeyError, ValueError, TypeError) as exc:
            if self.allow_deterministic_fallback:
                return deterministic_normalize_rows(
                    agency=agency,
                    agency_id=agency_id,
                    source_url=source_url,
                    source_title=source_title,
                    source_published_at=source_published_at,
                    source_hash_sha256=source_hash_sha256,
                    rows=rows,
                )
            raise PipelineConfigError(f"LLM normalization failed: {exc}") from exc

    async def _normalize_with_llm(
        self,
        *,
        agency_id: UUID,
        agency: Agency,
        source_url: str,
        source_title: str,
        source_published_at: date | None,
        source_hash_sha256: str,
        rows: list[ParsedExpenseRow],
    ) -> list[NormalizedVisit]:
        payload = {
            "agency_id": str(agency_id),
            "source_url": source_url,
            "source_title": source_title,
            "source_published_at": source_published_at.isoformat() if source_published_at else None,
            "source_hash_sha256": source_hash_sha256,
            "rows": [row.model_dump(mode="json") for row in rows],
            "required_visit_fields": [
                "visit_date",
                "amount",
                "party_size",
                "purpose",
                "department_name",
                "rank_label",
                "representative",
                "payment_method",
                "expense_category",
                "place_raw",
                "raw_excerpt",
                "confidence",
            ],
        }
        prompt = json.dumps(
            {
                "system_prompt": _system_prompt_for(agency),
                "user_prompt": (
                    f"Normalize these {agency.parent_region} public expense rows. "
                    "Return JSON only.\n\n"
                    + json.dumps(payload, ensure_ascii=False)
                ),
            },
            ensure_ascii=False,
        )
        result = await self._llm_client.extract(
            task=TaskType.TABLE_NORMALIZE,
            prompt=prompt,
            schema={"required": ["visits"]},
            timeout=60.0,
        )

        visits = []
        for visit in result.payload.get("visits", []):
            visit = _coerce_visit_payload(visit)
            visit.setdefault("agency_id", str(agency_id))
            visit.setdefault("source_url", source_url)
            visit.setdefault("source_title", source_title)
            visit.setdefault(
                "source_published_at", source_published_at.isoformat() if source_published_at else None
            )
            visit.setdefault("source_hash_sha256", source_hash_sha256)
            visit["raw_excerpt"] = sanitize_raw_excerpt(visit.get("raw_excerpt"))
            visits.append(NormalizedVisit.model_validate(visit))
        return visits


def _coerce_visit_payload(visit: Any) -> dict[str, Any]:
    if not isinstance(visit, dict):
        raise TypeError("visit payload must be an object")
    coerced = dict(visit)

    visit_date = coerced.get("visit_date")
    if isinstance(visit_date, str) and "T" in visit_date:
        coerced["visit_date"] = visit_date.split("T", 1)[0]

    source_published_at = coerced.get("source_published_at")
    if isinstance(source_published_at, str) and "T" in source_published_at:
        coerced["source_published_at"] = source_published_at.split("T", 1)[0]

    place_raw = coerced.get("place_raw")
    if isinstance(place_raw, str):
        coerced["place_raw"] = {"name": place_raw.strip(), "address_hint": None}
    elif isinstance(place_raw, dict):
        place_raw = dict(place_raw)
        if "name" not in place_raw:
            for key in ("place_name", "place", "name_raw"):
                if place_raw.get(key):
                    place_raw["name"] = place_raw[key]
                    break
        place_raw.setdefault("address_hint", place_raw.get("address") or place_raw.get("address_hint"))
        coerced["place_raw"] = place_raw
    else:
        for key in ("place_name", "place", "place_text"):
            if coerced.get(key):
                coerced["place_raw"] = {"name": str(coerced[key]).strip(), "address_hint": None}
                break

    confidence = coerced.get("confidence")
    if confidence is None:
        coerced["confidence"] = _DEFAULT_LLM_CONFIDENCE
        return coerced
    if isinstance(confidence, str):
        confidence_text = confidence.strip().lower()
        try:
            coerced["confidence"] = float(confidence_text)
        except ValueError:
            if confidence_text in _CONFIDENCE_LABELS:
                coerced["confidence"] = _CONFIDENCE_LABELS[confidence_text]
    return coerced

__all__ = ["_loads_json_response", "_repair_common_json_response"]
