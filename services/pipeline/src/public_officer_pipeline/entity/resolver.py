from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Any

import httpx

from public_officer_pipeline.entity.policy import (
    DefaultPlaceResolutionPolicy,
    PlaceResolutionPolicy,
)
from public_officer_pipeline.models import PipelineConfigError, PlaceRaw, ResolvedPlace

KAKAO_KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
KAKAO_ADDRESS_URL = "https://dapi.kakao.com/v2/local/search/address.json"
KAKAO_CACHE_TTL_SECONDS = 60 * 60 * 24 * 7


class KakaoResolver:
    def __init__(
        self,
        *,
        kakao_rest_key: str | None = None,
        cache_path: Path | None = None,
        allow_unmatched_fallback: bool = False,
        policy: PlaceResolutionPolicy | None = None,
    ) -> None:
        self.kakao_rest_key = kakao_rest_key or os.getenv("KAKAO_REST_KEY")
        self.allow_unmatched_fallback = allow_unmatched_fallback
        self.cache_path = cache_path or Path("services/pipeline/pipeline_state.db")
        self.policy = policy or DefaultPlaceResolutionPolicy()
        self._init_cache()

    async def resolve(self, place: PlaceRaw) -> ResolvedPlace:
        cache_key = f"{place.name}|{place.address_hint or ''}"
        cached = self._cache_get(cache_key)
        if cached:
            return ResolvedPlace.model_validate_json(cached)

        if not self.kakao_rest_key:
            if not self.allow_unmatched_fallback:
                raise PipelineConfigError("KAKAO_REST_KEY is required for place resolution")
            resolved = self._fallback(place, None, None)
            self._cache_set(cache_key, resolved.model_dump_json())
            return resolved

        async with httpx.AsyncClient(timeout=20.0) as client:
            address_documents = await self._search_address(client, place)
            if address_documents:
                source_coordinates = self._extract_document_coordinates(address_documents[0])
            else:
                source_coordinates = (None, None)
            self.policy.source_coordinates = source_coordinates
            documents = await self._search_kakao(client, place)

        if documents:
            candidates = [
                document
                for document in documents
                if self.policy.validate_candidate(
                    place,
                    {
                        **document,
                        "_validation_latitude": source_coordinates[0],
                        "_validation_longitude": source_coordinates[1],
                    },
                )
            ]
            best = self.policy.choose_best_kakao_document(place, candidates)
            if best is not None:
                resolved = self.policy.from_kakao_document(place, best)
            else:
                resolved = self.policy.fallback(
                    place, latitude=source_coordinates[0], longitude=source_coordinates[1]
                )
        elif address_documents:
            resolved = self.policy.from_kakao_document(place, address_documents[0])
        else:
            resolved = self.policy.fallback(
                place, latitude=source_coordinates[0], longitude=source_coordinates[1]
            )

        self._cache_set(cache_key, resolved.model_dump_json())
        return resolved

    async def _search_kakao(self, client: httpx.AsyncClient, place: PlaceRaw) -> list[dict[str, Any]]:
        for query in self.policy.candidate_queries(place):
            response = await client.get(
                KAKAO_KEYWORD_URL,
                params={"query": query, "size": 5},
                headers={"Authorization": f"KakaoAK {self.kakao_rest_key}"},
            )
            response.raise_for_status()
            documents = response.json().get("documents", [])
            if documents:
                return documents
        return []

    async def _search_address(self, client: httpx.AsyncClient, place: PlaceRaw) -> list[dict[str, Any]]:
        if not place.address_hint:
            return []
        response = await client.get(
            KAKAO_ADDRESS_URL,
            params={"query": place.address_hint, "size": 1},
            headers={"Authorization": f"KakaoAK {self.kakao_rest_key}"},
        )
        response.raise_for_status()
        return response.json().get("documents", [])

    def _fallback(self, place: PlaceRaw, latitude: float | None, longitude: float | None) -> ResolvedPlace:
        return self.policy.fallback(place, latitude=latitude, longitude=longitude)

    def _extract_document_coordinates(self, document: dict[str, Any]) -> tuple[float | None, float | None]:
        latitude = document.get("y")
        longitude = document.get("x")
        if latitude is not None and longitude is not None:
            try:
                return float(latitude), float(longitude)
            except (TypeError, ValueError):
                pass
        road_address = document.get("road_address")
        address = document.get("address")
        if isinstance(road_address, dict):
            y = road_address.get("y")
            x = road_address.get("x")
            try:
                return (float(y), float(x))
            except (TypeError, ValueError):
                pass
        if isinstance(address, dict):
            y = address.get("y")
            x = address.get("x")
            try:
                return (float(y), float(x))
            except (TypeError, ValueError):
                pass
        return (None, None)

    def _init_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.cache_path) as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS kakao_cache (cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )
            existing_columns = {
                row[1]
                for row in con.execute("PRAGMA table_info(kakao_cache)").fetchall()
            }
            if "created_at" not in existing_columns:
                con.execute("ALTER TABLE kakao_cache ADD COLUMN created_at INTEGER")

    def _cache_get(self, cache_key: str) -> str | None:
        with sqlite3.connect(self.cache_path) as con:
            row = con.execute(
                "SELECT payload, created_at FROM kakao_cache WHERE cache_key = ?", (cache_key,)
            ).fetchone()
            if not row:
                return None

            payload, created_at = row
            if created_at is None:
                con.execute("DELETE FROM kakao_cache WHERE cache_key = ?", (cache_key,))
                return None

            if self._cache_expired(int(created_at)):
                con.execute("DELETE FROM kakao_cache WHERE cache_key = ?", (cache_key,))
                return None
            return payload

    def _cache_expired(self, created_at: int) -> bool:
        return (self._now_ts() - created_at) >= KAKAO_CACHE_TTL_SECONDS

    def _cache_set(self, cache_key: str, payload: str) -> None:
        with sqlite3.connect(self.cache_path) as con:
            con.execute(
                "INSERT INTO kakao_cache (cache_key, payload, created_at) VALUES (?, ?, ?) "
                "ON CONFLICT(cache_key) DO UPDATE SET payload = excluded.payload, created_at = excluded.created_at",
                (cache_key, payload, self._now_ts()),
            )

    def _now_ts(self) -> int:
        return int(time.time())
