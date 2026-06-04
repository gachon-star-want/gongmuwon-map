from __future__ import annotations

import atexit
import os
import time
from pathlib import Path
from typing import Any

import aiosqlite
import httpx

from public_officer_pipeline.entity.policy import (
    DefaultPlaceResolutionPolicy,
    PlaceResolutionPolicy,
)
from public_officer_pipeline.models import PipelineConfigError, PlaceRaw, ResolvedPlace, Agency

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
        self._cache_db: aiosqlite.Connection | None = None
        self._http_client = httpx.AsyncClient(timeout=20.0)

        # Load agency coordinates
        import json
        self.agency_coordinates = {}
        coords_path = Path(__file__).parent / "agency_coordinates.json"
        if coords_path.exists():
            with open(coords_path, "r", encoding="utf-8") as f:
                self.agency_coordinates = json.load(f)

    async def resolve(self, place: PlaceRaw, agency: Agency | None = None) -> ResolvedPlace:
        # Cache key definition
        # Update cache key if address_hint is missing and agency is provided, to avoid cache collision
        if not place.address_hint and agency:
            cache_key = f"{place.name}||{agency.id}"
        else:
            cache_key = f"{place.name}|{place.address_hint or ''}"

        cached = await self._cache_get(cache_key)
        if cached:
            return ResolvedPlace.model_validate_json(cached)

        if not self.kakao_rest_key:
            if not self.allow_unmatched_fallback:
                raise PipelineConfigError("KAKAO_REST_KEY is required for place resolution")
            resolved = self._fallback(place, None, None)
            await self._cache_set(cache_key, resolved.model_dump_json())
            return resolved

        # Get agency coords
        agency_coords = None
        if agency:
            agency_data = self.agency_coordinates.get(str(agency.id))
            if agency_data:
                lat = agency_data.get("latitude")
                lon = agency_data.get("longitude")
                if lat is not None and lon is not None:
                    agency_coords = (float(lat), float(lon))

        address_documents = await self._search_address(place)
        if address_documents:
            source_coordinates = self._extract_document_coordinates(address_documents[0])
        else:
            source_coordinates = (None, None)
        self.policy.source_coordinates = source_coordinates
        documents = await self._search_kakao(place, agency_coords=agency_coords)

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
                    agency=agency,
                )
            ]
            best = self.policy.choose_best_kakao_document(place, candidates)
            if best is not None:
                resolved = self.policy.from_kakao_document(place, best)
            else:
                lat = source_coordinates[0]
                lng = source_coordinates[1]
                if (lat is None or lng is None) and agency_coords:
                    lat, lng = agency_coords
                resolved = self.policy.fallback(
                    place, latitude=lat, longitude=lng
                )
        elif address_documents:
            resolved = self.policy.from_kakao_document(place, address_documents[0])
        else:
            lat = source_coordinates[0]
            lng = source_coordinates[1]
            if (lat is None or lng is None) and agency_coords:
                lat, lng = agency_coords
            resolved = self.policy.fallback(
                place, latitude=lat, longitude=lng
            )

        await self._cache_set(cache_key, resolved.model_dump_json())
        return resolved

    async def _search_kakao(
        self,
        place: PlaceRaw,
        agency_coords: tuple[float, float] | None = None,
    ) -> list[dict[str, Any]]:
        for query in self.policy.candidate_queries(place):
            # Prioritize local search if address_hint is missing and agency coordinates are available
            if not place.address_hint and agency_coords:
                lat, lon = agency_coords
                try:
                    response = await self._http_client.get(
                        KAKAO_KEYWORD_URL,
                        params={
                            "query": query,
                            "size": 5,
                            "x": str(lon),
                            "y": str(lat),
                            "radius": 20000,
                        },
                        headers={"Authorization": f"KakaoAK {self.kakao_rest_key}"},
                    )
                    response.raise_for_status()
                    documents = response.json().get("documents", [])
                    if documents:
                        return documents
                except httpx.HTTPError:
                    pass

            response = await self._http_client.get(
                KAKAO_KEYWORD_URL,
                params={"query": query, "size": 5},
                headers={"Authorization": f"KakaoAK {self.kakao_rest_key}"},
            )
            response.raise_for_status()
            documents = response.json().get("documents", [])
            if documents:
                return documents
        return []

    async def _search_address(self, place: PlaceRaw) -> list[dict[str, Any]]:
        if not place.address_hint:
            return []
        response = await self._http_client.get(
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

    async def _ensure_cache(self) -> None:
        if self._cache_db is not None:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache_db = await aiosqlite.connect(str(self.cache_path))
        await self._cache_db.execute(
            "CREATE TABLE IF NOT EXISTS kakao_cache (cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
        cursor = await self._cache_db.execute("PRAGMA table_info(kakao_cache)")
        rows = await cursor.fetchall()
        existing_columns = {row[1] for row in rows}
        if "created_at" not in existing_columns:
            await self._cache_db.execute("ALTER TABLE kakao_cache ADD COLUMN created_at INTEGER")
        await self._cache_db.commit()

    async def _cache_get(self, cache_key: str) -> str | None:
        await self._ensure_cache()
        cursor = await self._cache_db.execute(
            "SELECT payload, created_at FROM kakao_cache WHERE cache_key = ?", (cache_key,)
        )
        row = await cursor.fetchone()
        if not row:
            return None

        payload, created_at = row
        if created_at is None:
            await self._cache_db.execute("DELETE FROM kakao_cache WHERE cache_key = ?", (cache_key,))
            await self._cache_db.commit()
            return None

        if self._cache_expired(int(created_at)):
            await self._cache_db.execute("DELETE FROM kakao_cache WHERE cache_key = ?", (cache_key,))
            await self._cache_db.commit()
            return None
        return payload

    def _cache_expired(self, created_at: int) -> bool:
        return (self._now_ts() - created_at) >= KAKAO_CACHE_TTL_SECONDS

    async def _cache_set(self, cache_key: str, payload: str) -> None:
        await self._ensure_cache()
        await self._cache_db.execute(
            "INSERT INTO kakao_cache (cache_key, payload, created_at) VALUES (?, ?, ?) "
            "ON CONFLICT(cache_key) DO UPDATE SET payload = excluded.payload, created_at = excluded.created_at",
            (cache_key, payload, self._now_ts()),
        )
        await self._cache_db.commit()

    def _now_ts(self) -> int:
        return int(time.time())

    async def close(self) -> None:
        await self._http_client.aclose()
        if self._cache_db is not None:
            await self._cache_db.close()
            self._cache_db = None
