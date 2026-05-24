from __future__ import annotations

import json
import os
import re
from datetime import date
from json import JSONDecodeError
from uuid import UUID

import httpx

from public_officer_pipeline.models import NormalizedVisit, ParsedExpenseRow, PipelineConfigError
from public_officer_pipeline.normalizer.rules import deterministic_normalize_rows


SYSTEM_PROMPT = """You normalize Korean public expense execution records into JSON.

Masking rules are mandatory:
1. Fill representative only for elected ranks: 시장, 구청장, 시의원, 구의원.
2. For appointed ranks such as 부시장, 국장, 과장, 팀장, 담당관, 전문위원, set representative to null.
3. For 5급 이하 or staff groups, set rank_label to "5급 이하" and keep only department-level labels.
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
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
        self.allow_deterministic_fallback = allow_deterministic_fallback

    async def normalize_rows(
        self,
        *,
        agency_id: UUID,
        source_url: str,
        source_title: str,
        source_published_at: date | None,
        source_hash_sha256: str,
        rows: list[ParsedExpenseRow],
    ) -> list[NormalizedVisit]:
        if not rows:
            return []
        if not self.anthropic_api_key:
            if self.allow_deterministic_fallback:
                return deterministic_normalize_rows(
                    agency_id=agency_id,
                    source_url=source_url,
                    source_title=source_title,
                    source_published_at=source_published_at,
                    source_hash_sha256=source_hash_sha256,
                    rows=rows,
                )
            raise PipelineConfigError("ANTHROPIC_API_KEY is required for LLM normalization")
        try:
            return await self._normalize_with_anthropic(
                agency_id=agency_id,
                source_url=source_url,
                source_title=source_title,
                source_published_at=source_published_at,
                source_hash_sha256=source_hash_sha256,
                rows=rows,
            )
        except (JSONDecodeError, KeyError, ValueError) as exc:
            if self.allow_deterministic_fallback:
                return deterministic_normalize_rows(
                    agency_id=agency_id,
                    source_url=source_url,
                    source_title=source_title,
                    source_published_at=source_published_at,
                    source_hash_sha256=source_hash_sha256,
                    rows=rows,
                )
            raise PipelineConfigError(f"LLM normalization returned invalid JSON: {exc}") from exc

    async def _normalize_with_anthropic(
        self,
        *,
        agency_id: UUID,
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
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 8192,
                    "temperature": 0,
                    "system": SYSTEM_PROMPT,
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                "Normalize these Seoul public expense rows. "
                                "Return JSON only.\n\n"
                                + json.dumps(payload, ensure_ascii=False)
                            ),
                        }
                    ],
                },
            )
            response.raise_for_status()
        body = response.json()
        text = "".join(block.get("text", "") for block in body.get("content", []) if block.get("type") == "text")
        parsed = _loads_json_response(text)
        visits = []
        for visit in parsed.get("visits", []):
            visit.setdefault("agency_id", str(agency_id))
            visit.setdefault("source_url", source_url)
            visit.setdefault("source_title", source_title)
            visit.setdefault(
                "source_published_at", source_published_at.isoformat() if source_published_at else None
            )
            visit.setdefault("source_hash_sha256", source_hash_sha256)
            visits.append(NormalizedVisit.model_validate(visit))
        return visits


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

    return json.loads(stripped)
