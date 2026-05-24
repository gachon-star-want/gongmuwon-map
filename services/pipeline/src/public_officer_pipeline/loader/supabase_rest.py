from __future__ import annotations

import os
from datetime import date
from typing import Any
from uuid import UUID

import httpx

from public_officer_pipeline.models import Agency, NormalizedVisit, PipelineConfigError, ResolvedPlace


class SupabaseRestLoader:
    def __init__(self, *, supabase_url: str | None = None, service_role_key: str | None = None) -> None:
        self.supabase_url = (supabase_url or os.getenv("SUPABASE_URL") or "").rstrip("/")
        self.service_role_key = service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not self.supabase_url or not self.service_role_key:
            raise PipelineConfigError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for loading")

    async def load(
        self,
        *,
        agency: Agency,
        source_url: str,
        source_title: str,
        source_published_at: date | None,
        source_hash_sha256: str,
        resolved_places: dict[str, ResolvedPlace],
        visits: list[NormalizedVisit],
    ) -> tuple[int, int, int]:
        async with httpx.AsyncClient(timeout=30.0, headers=self._headers()) as client:
            await self._upsert_one(
                client,
                "agencies",
                agency.model_dump(mode="json"),
                "kind,parent_region,sub_region",
            )
            source = await self._upsert_one(
                client,
                "sources",
                {
                    "agency_id": str(agency.id),
                    "url": source_url,
                    "title": source_title,
                    "published_at": source_published_at.isoformat() if source_published_at else None,
                    "file_kind": "html",
                    "hash_sha256": source_hash_sha256,
                },
                "agency_id,hash_sha256",
            )
            place_ids: dict[str, UUID] = {}
            for place in resolved_places.values():
                inserted = await self._upsert_one(
                    client,
                    "places",
                    {
                        "kakao_place_id": place.kakao_place_id,
                        "natural_key": place.natural_key,
                        "name": place.name,
                        "road_address": place.road_address,
                        "jibun_address": place.jibun_address,
                        "road_address_part": place.road_address_part,
                        "latitude": place.latitude,
                        "longitude": place.longitude,
                        "category": place.category,
                        "phone": place.phone,
                    },
                    "natural_key",
                )
                place_ids[place.natural_key] = UUID(inserted["id"])
            visit_count = 0
            for visit in visits:
                place_id = place_ids[resolved_places[visit.place_raw.model_dump_json()].natural_key]
                await self._upsert_one(
                    client,
                    "place_visits",
                    {
                        "place_id": str(place_id),
                        "agency_id": str(visit.agency_id),
                        "source_id": source["id"],
                        "visit_date": visit.visit_date.isoformat(),
                        "amount": visit.amount,
                        "party_size": visit.party_size,
                        "purpose": visit.purpose,
                        "department_name": visit.department_name,
                        "rank_label": visit.rank_label,
                        "representative": visit.representative,
                        "payment_method": visit.payment_method,
                        "expense_category": visit.expense_category,
                        "raw_excerpt": visit.raw_excerpt,
                        "extractor_model": "claude-haiku-4-5",
                        "extractor_confidence": visit.confidence,
                    },
                    "agency_id,visit_date,place_id,amount,department_name",
                )
                visit_count += 1
        return 1, len(place_ids), visit_count

    async def _upsert_one(
        self,
        client: httpx.AsyncClient,
        table: str,
        payload: dict[str, Any],
        on_conflict: str,
    ) -> dict[str, Any]:
        response = await client.post(
            f"{self.supabase_url}/rest/v1/{table}",
            params={"on_conflict": on_conflict},
            headers={"Prefer": "resolution=merge-duplicates,return=representation"},
            json=payload,
        )
        response.raise_for_status()
        body = response.json()
        if not body:
            raise RuntimeError(f"Supabase upsert returned no representation for {table}")
        return body[0]

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self.service_role_key or "",
            "authorization": f"Bearer {self.service_role_key}",
            "content-type": "application/json",
        }
