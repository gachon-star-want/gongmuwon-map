from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod
from typing import Any

from public_officer_pipeline.entity.geohash import encode_geohash
from public_officer_pipeline.models import PlaceRaw, ResolvedPlace

_SEOUL_REGION_RE = re.compile(r"(서울(?:특별시)?|서울)\s+([가-힣]+[구군시])")
_GYEONGGI_REGION_RE = re.compile(r"(경기(?:도)?|경기도)\s+([가-힣]+[시군구])")
_INCHEON_REGION_RE = re.compile(r"(인천(?:광역시)?|인천)\s+([가-힣]+[시군구])")


def normalize_name(value: str) -> str:
    return re.sub(r"[\s㈜주식회사()（）·.,-]+", "", value).lower()


def normalize_address(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[\s·.,-]", "", value)


def _normalize_address_tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    compact = normalize_address(value)
    compact = re.sub(r"[^가-힣A-Za-z0-9]+", " ", compact)
    tokens = compact.split()
    return {token for token in tokens if token}


def _candidate_query_names(name: str) -> list[str]:
    cleaned = re.sub(r"[()（）㈜]", " ", name)
    cleaned = re.sub(r"\b주식회사\b|\b유한회사\b|\b합자회사\b|\b합명회사\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return []
    tokens = cleaned.split()
    candidates = [cleaned]
    if len(tokens) >= 2:
        candidates.append(" ".join(tokens[-2:]))
    if len(tokens) >= 3:
        candidates.append(" ".join(tokens[-3:]))
    return list(dict.fromkeys(candidates))


def road_address_part(address: str | None) -> str | None:
    if not address:
        return None
    for pattern, region in (
        (_SEOUL_REGION_RE, "서울"),
        (_GYEONGGI_REGION_RE, "경기"),
        (_INCHEON_REGION_RE, "인천"),
    ):
        match = pattern.search(address)
        if match:
            return f"{region} {match.group(2)}"
    return None


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def natural_key(
    name: str,
    address: str | None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> str:
    normalized_name = normalize_name(name)
    if latitude is not None and longitude is not None:
        location_key = encode_geohash(latitude=latitude, longitude=longitude, precision=7)
    else:
        location_key = normalize_address(address)
    base = f"{normalized_name}|{location_key}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def _extract_document_address(document: dict[str, Any]) -> tuple[str | None, str | None]:
    road_address = document.get("road_address_name")
    if not road_address:
        road_address = (
            document.get("road_address", {}).get("address_name")
            if isinstance(document.get("road_address"), dict)
            else None
        )
    jibun_address = document.get("address_name")
    if not jibun_address:
        jibun_address = (
            document.get("address", {}).get("address_name")
            if isinstance(document.get("address"), dict)
            else None
        )
    return road_address, jibun_address


def _extract_document_coordinates(document: dict[str, Any]) -> tuple[float | None, float | None]:
    latitude = _to_float(document.get("y"))
    longitude = _to_float(document.get("x"))
    if latitude is None or longitude is None:
        road_address = document.get("road_address")
        address = document.get("address")
        if isinstance(road_address, dict):
            latitude = _to_float(road_address.get("y")) if latitude is None else latitude
            longitude = _to_float(road_address.get("x")) if longitude is None else longitude
        if isinstance(address, dict):
            if latitude is None:
                latitude = _to_float(address.get("y"))
            if longitude is None:
                longitude = _to_float(address.get("x"))
    return latitude, longitude


def _haversine_meters(
    first_latitude: float,
    first_longitude: float,
    second_latitude: float,
    second_longitude: float,
) -> float:
    earth_radius = 6371000
    first_latitude_rad = math.radians(first_latitude)
    second_latitude_rad = math.radians(second_latitude)
    delta_lat = math.radians(second_latitude - first_latitude)
    delta_lon = math.radians(second_longitude - first_longitude)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(first_latitude_rad) * math.cos(second_latitude_rad) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * earth_radius * math.asin(math.sqrt(a))


class PlaceResolutionPolicy(ABC):
    @abstractmethod
    def candidate_queries(self, place: PlaceRaw) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def choose_best_kakao_document(self, place: PlaceRaw, documents: list[dict[str, Any]]) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def validate_candidate(self, place: PlaceRaw, document: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def from_kakao_document(self, place: PlaceRaw, document: dict[str, Any]) -> ResolvedPlace:
        raise NotImplementedError

    @abstractmethod
    def fallback(
        self,
        place: PlaceRaw,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> ResolvedPlace:
        raise NotImplementedError


class DefaultPlaceResolutionPolicy(PlaceResolutionPolicy):
    def __init__(
        self,
        source_coordinates: tuple[float, float] | None = None,
        validation_threshold_meters: float = 300.0,
    ):
        self.source_coordinates = source_coordinates
        self.validation_threshold_meters = validation_threshold_meters

    def candidate_queries(self, place: PlaceRaw) -> list[str]:
        names = _candidate_query_names(place.name)
        queries: list[str] = []
        for name in names:
            if place.address_hint:
                queries.append(f"{name} {place.address_hint}".strip())
            queries.append(name)
        return list(dict.fromkeys(query for query in queries if query))

    def choose_best_kakao_document(self, place: PlaceRaw, documents: list[dict[str, Any]]) -> dict[str, Any] | None:
        del place
        if not documents:
            return None
        food_docs = [document for document in documents if document.get("category_group_code") == "FD6"]
        return (food_docs or documents)[0]

    def validate_candidate(self, place: PlaceRaw, document: dict[str, Any]) -> bool:
        validation_latitude = _to_float(document.get("_validation_latitude"))
        validation_longitude = _to_float(document.get("_validation_longitude"))
        if self.source_coordinates and (validation_latitude is None or validation_longitude is None):
            validation_latitude = self.source_coordinates[0]
            validation_longitude = self.source_coordinates[1]

        road_address, jibun_address = _extract_document_address(document)
        candidate_part = road_address_part(road_address or jibun_address)

        if validation_latitude is not None and validation_longitude is not None:
            candidate_latitude, candidate_longitude = _extract_document_coordinates(document)
            if candidate_latitude is not None and candidate_longitude is not None:
                distance = _haversine_meters(
                    validation_latitude, validation_longitude, candidate_latitude, candidate_longitude
                )
                return distance <= self.validation_threshold_meters

        if not place.address_hint:
            return True
        source_part = road_address_part(place.address_hint)
        if source_part and candidate_part and source_part != candidate_part:
            return False

        source_tokens = _normalize_address_tokens(place.address_hint)
        candidate_tokens = _normalize_address_tokens(road_address or jibun_address)
        if not source_tokens or not candidate_tokens:
            return True
        return bool(source_tokens.intersection(candidate_tokens))

    def from_kakao_document(self, place: PlaceRaw, document: dict[str, Any]) -> ResolvedPlace:
        road_address, jibun_address = _extract_document_address(document)
        latitude, longitude = _extract_document_coordinates(document)
        address = road_address or jibun_address or place.address_hint
        place_id = document.get("id") or None
        return ResolvedPlace(
            kakao_place_id=place_id,
            natural_key=natural_key(place.name, address, latitude, longitude),
            name=document.get("place_name") or place.name,
            road_address=road_address,
            jibun_address=jibun_address,
            road_address_part=road_address_part(address),
            latitude=latitude,
            longitude=longitude,
            category=document.get("category_name") or None,
            phone=document.get("phone") or None,
            matched=bool(place_id),
            raw=document,
        )

    def fallback(
        self,
        place: PlaceRaw,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> ResolvedPlace:
        return ResolvedPlace(
            kakao_place_id=None,
            natural_key=natural_key(place.name, place.address_hint, latitude, longitude),
            name=place.name,
            road_address=place.address_hint,
            jibun_address=None,
            road_address_part=road_address_part(place.address_hint),
            latitude=latitude,
            longitude=longitude,
            category=None,
            phone=None,
            matched=False,
            raw={},
        )
