from __future__ import annotations

import hashlib
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

import httpx

from public_officer_pipeline.models import PipelineConfigError, PlaceRaw, ResolvedPlace


KAKAO_KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
KAKAO_ADDRESS_URL = "https://dapi.kakao.com/v2/local/search/address.json"
SEOUL_REGION_RE = re.compile(r"(서울(?:특별시)?|서울)\s+([가-힣]+구)")


class KakaoResolver:
    def __init__(
        self,
        *,
        kakao_rest_key: str | None = None,
        cache_path: Path | None = None,
        allow_unmatched_fallback: bool = False,
    ) -> None:
        self.kakao_rest_key = kakao_rest_key or os.getenv("KAKAO_REST_KEY")
        self.allow_unmatched_fallback = allow_unmatched_fallback
        self.cache_path = cache_path or Path("services/pipeline/pipeline_state.db")
        self._init_cache()

    async def resolve(self, place: PlaceRaw) -> ResolvedPlace:
        cache_key = f"{place.name}|{place.address_hint or ''}"
        cached = self._cache_get(cache_key)
        if cached:
            resolved = ResolvedPlace.model_validate_json(cached)
            if resolved.matched or not self.kakao_rest_key:
                return resolved
        if not self.kakao_rest_key:
            if not self.allow_unmatched_fallback:
                raise PipelineConfigError("KAKAO_REST_KEY is required for place resolution")
            resolved = self._fallback(place)
            self._cache_set(cache_key, resolved.model_dump_json())
            return resolved

        async with httpx.AsyncClient(timeout=20.0) as client:
            documents = await self._search_kakao(client, place)
            address_documents = [] if documents else await self._search_address(client, place)
        if documents:
            resolved = self._from_kakao(place, self._best_document(documents))
        elif address_documents:
            resolved = self._from_kakao_address(place, address_documents[0])
        else:
            resolved = self._fallback(place)
        self._cache_set(cache_key, resolved.model_dump_json())
        return resolved

    async def _search_kakao(self, client: httpx.AsyncClient, place: PlaceRaw) -> list[dict[str, Any]]:
        for query in kakao_queries(place):
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

    def _best_document(self, documents: list[dict[str, Any]]) -> dict[str, Any]:
        food = [doc for doc in documents if doc.get("category_group_code") == "FD6"]
        return (food or documents)[0]

    def _from_kakao(self, place: PlaceRaw, document: dict[str, Any]) -> ResolvedPlace:
        road_address = document.get("road_address_name") or None
        jibun_address = document.get("address_name") or None
        address = road_address or jibun_address or place.address_hint
        return ResolvedPlace(
            kakao_place_id=document.get("id") or None,
            natural_key=natural_key(place.name, address),
            name=document.get("place_name") or place.name,
            road_address=road_address,
            jibun_address=jibun_address,
            road_address_part=road_address_part(address),
            latitude=float(document["y"]) if document.get("y") else None,
            longitude=float(document["x"]) if document.get("x") else None,
            category=document.get("category_name") or None,
            phone=document.get("phone") or None,
            matched=True,
            raw=document,
        )

    def _from_kakao_address(self, place: PlaceRaw, document: dict[str, Any]) -> ResolvedPlace:
        road_address_doc = document.get("road_address") or {}
        address_doc = document.get("address") or {}
        road_address = document.get("road_address_name") or road_address_doc.get("address_name") or None
        jibun_address = document.get("address_name") or address_doc.get("address_name") or None
        address = road_address or jibun_address or place.address_hint
        latitude = document.get("y") or road_address_doc.get("y") or address_doc.get("y")
        longitude = document.get("x") or road_address_doc.get("x") or address_doc.get("x")
        return ResolvedPlace(
            kakao_place_id=None,
            natural_key=natural_key(place.name, address),
            name=place.name,
            road_address=road_address,
            jibun_address=jibun_address,
            road_address_part=road_address_part(address),
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            category=None,
            phone=None,
            matched=False,
            raw=document,
        )

    def _fallback(self, place: PlaceRaw) -> ResolvedPlace:
        return ResolvedPlace(
            kakao_place_id=None,
            natural_key=natural_key(place.name, place.address_hint),
            name=place.name,
            road_address=place.address_hint,
            road_address_part=road_address_part(place.address_hint),
            matched=False,
        )

    def _init_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.cache_path) as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS kakao_cache (cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )

    def _cache_get(self, cache_key: str) -> str | None:
        with sqlite3.connect(self.cache_path) as con:
            row = con.execute("SELECT payload FROM kakao_cache WHERE cache_key = ?", (cache_key,)).fetchone()
            return row[0] if row else None

    def _cache_set(self, cache_key: str, payload: str) -> None:
        with sqlite3.connect(self.cache_path) as con:
            con.execute(
                "INSERT INTO kakao_cache (cache_key, payload) VALUES (?, ?) "
                "ON CONFLICT(cache_key) DO UPDATE SET payload = excluded.payload",
                (cache_key, payload),
            )


def normalize_name(value: str) -> str:
    return re.sub(r"[\s㈜주식회사()（）·.,-]+", "", value).lower()


def kakao_queries(place: PlaceRaw) -> list[str]:
    names = _candidate_query_names(place.name)
    queries: list[str] = []
    for name in names:
        if place.address_hint:
            queries.append(f"{name} {place.address_hint}".strip())
        queries.append(name)
    return list(dict.fromkeys(query for query in queries if query))


def _candidate_query_names(name: str) -> list[str]:
    cleaned = re.sub(r"[()（）㈜]", " ", name)
    cleaned = re.sub(r"\b주식회사\b|\b유한회사\b|\b합자회사\b|\b합명회사\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    tokens = cleaned.split()
    candidates = [cleaned]
    if len(tokens) >= 2:
        candidates.append(" ".join(tokens[-2:]))
    if len(tokens) >= 3:
        candidates.append(" ".join(tokens[-3:]))
    return list(dict.fromkeys(candidates))


def natural_key(name: str, address: str | None) -> str:
    base = f"{normalize_name(name)}|{address or ''}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def road_address_part(address: str | None) -> str | None:
    if not address:
        return None
    match = SEOUL_REGION_RE.search(address)
    if not match:
        return None
    return f"서울 {match.group(2)}"
