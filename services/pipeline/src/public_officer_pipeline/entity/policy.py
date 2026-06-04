from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod
from typing import Any

import json
from pathlib import Path
from public_officer_pipeline.entity.geohash import encode_geohash
from public_officer_pipeline.models import PlaceRaw, ResolvedPlace, Agency, GovTier

# Load agency coordinates
_AGENCY_COORDINATES: dict[str, dict[str, Any]] = {}
try:
    _coords_path = Path(__file__).parent / "agency_coordinates.json"
    if _coords_path.exists():
        with open(_coords_path, "r", encoding="utf-8") as _f:
            _AGENCY_COORDINATES = json.load(_f)
except Exception:
    pass

_SEOUL_REGION_RE = re.compile(r"(서울(?:특별시)?|서울)\s+([가-힣]+[구군시])")
_GYEONGGI_REGION_RE = re.compile(r"(경기(?:도)?|경기도)\s+([가-힣]+[시군구])")
_INCHEON_REGION_RE = re.compile(r"(인천(?:광역시)?|인천)\s+([가-힣]+[시군구])")
_PLACEHOLDER_PLACE_KEYS = {
    "unknown",
    "none",
    "na",
    "정보없음",
    "미상",
    "해당없음",
    "없음",
    "장소없음",
    "불명",
}
_RESTAURANT_CATEGORY_HINTS = (
    "음식점",
    "한식",
    "중식",
    "일식",
    "양식",
    "분식",
    "뷔페",
    "패스트푸드",
    "간식",
    "카페",
    "커피",
    "제과",
    "베이커리",
)
_LARGE_CHAIN_BRANDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("스타벅스", ("스타벅스", "starbucks")),
    ("투썸플레이스", ("투썸플레이스", "투썸", "twosome")),
    ("메가커피", ("메가커피", "메가mgc커피", "mega coffee", "megacoffee")),
    ("컴포즈커피", ("컴포즈커피", "컴포즈", "compose coffee", "composecoffee")),
    ("파리바게뜨", ("파리바게뜨", "파리바게트", "paris baguette", "parisbaguette")),
    ("맥도날드", ("맥도날드", "mcdonald", "mcdonalds", "mcDonald's")),
    ("버거킹", ("버거킹", "burger king", "burgerking")),
    ("롯데리아", ("롯데리아", "lotteria")),
    ("써브웨이", ("써브웨이", "서브웨이", "subway")),
    ("이디야커피", ("이디야", "ediya")),
    ("빽다방", ("빽다방", "paik")),
    ("커피빈", ("커피빈", "coffee bean", "coffeebean")),
    ("할리스", ("할리스", "hollys")),
    ("배스킨라빈스", ("배스킨라빈스", "베스킨라빈스", "baskin")),
    ("던킨", ("던킨", "dunkin")),
    ("KFC", ("kfc",)),
    ("맘스터치", ("맘스터치", "mom's touch", "momstouch")),
)


def normalize_name(value: str) -> str:
    return re.sub(r"[\s㈜주식회사()（）·.,-]+", "", value).lower()


def is_valid_place_name(value: str | None) -> bool:
    if value is None:
        return False
    key = _placeholder_key(value)
    return bool(key) and key not in _PLACEHOLDER_PLACE_KEYS


def classify_large_chain_brand(value: str | None) -> str | None:
    if not value:
        return None
    key = _brand_key(value)
    for brand, aliases in _LARGE_CHAIN_BRANDS:
        if any(_brand_key(alias) in key for alias in aliases):
            return brand
    return None


def is_restaurant_like_category(category_group_code: str | None, category_name: str | None) -> bool:
    if category_group_code == "FD6":
        return True
    if category_group_code and category_group_code != "FD6":
        return False
    if not category_name:
        return True
    return any(hint in category_name for hint in _RESTAURANT_CATEGORY_HINTS)


def normalize_address(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[\s·.,-]", "", value)


def _placeholder_key(value: str) -> str:
    return re.sub(r"[\s./_()（）-]+", "", value).lower()


def _brand_key(value: str) -> str:
    return re.sub(r"[^0-9a-zA-Z가-힣]+", "", value).lower()


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
    def validate_candidate(self, place: PlaceRaw, document: dict[str, Any], agency: Agency | None = None) -> bool:
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

    def validate_candidate(self, place: PlaceRaw, document: dict[str, Any], agency: Agency | None = None) -> bool:
        validation_latitude = _to_float(document.get("_validation_latitude"))
        validation_longitude = _to_float(document.get("_validation_longitude"))
        if self.source_coordinates and (validation_latitude is None or validation_longitude is None):
            validation_latitude = self.source_coordinates[0]
            validation_longitude = self.source_coordinates[1]

        road_address, jibun_address = _extract_document_address(document)
        candidate_part = road_address_part(road_address or jibun_address)

        # Distance verification when address_hint is missing/empty and agency coords are available
        if not place.address_hint and agency:
            agency_data = _AGENCY_COORDINATES.get(str(agency.id))
            if agency_data:
                agency_lat = _to_float(agency_data.get("latitude"))
                agency_lon = _to_float(agency_data.get("longitude"))
                if agency_lat is not None and agency_lon is not None:
                    candidate_latitude, candidate_longitude = _extract_document_coordinates(document)
                    if candidate_latitude is not None and candidate_longitude is not None:
                        distance = _haversine_meters(
                            agency_lat, agency_lon, candidate_latitude, candidate_longitude
                        )
                        if distance > 50000.0:
                            is_national_or_constitutional = agency.gov_tier in (
                                GovTier.NATIONAL,
                                GovTier.CONSTITUTIONAL,
                            )
                            is_large_chain = classify_large_chain_brand(document.get("place_name")) is not None
                            if not (is_national_or_constitutional or is_large_chain):
                                return False

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
        name = document.get("place_name") or place.name
        category_name = document.get("category_name") or None
        chain_brand = classify_large_chain_brand(name)
        return ResolvedPlace(
            kakao_place_id=place_id,
            natural_key=natural_key(place.name, address, latitude, longitude),
            name=name,
            road_address=road_address,
            jibun_address=jibun_address,
            road_address_part=road_address_part(address),
            latitude=latitude,
            longitude=longitude,
            category=category_name,
            phone=document.get("phone") or None,
            matched=bool(place_id),
            valid_place=is_valid_place_name(name),
            is_restaurant_like=is_restaurant_like_category(
                document.get("category_group_code"),
                category_name,
            ),
            is_chain=chain_brand is not None,
            is_large_chain=chain_brand is not None,
            chain_brand=chain_brand,
            chain_scale="대형전국체인" if chain_brand else None,
            raw=document,
        )

    def fallback(
        self,
        place: PlaceRaw,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> ResolvedPlace:
        chain_brand = classify_large_chain_brand(place.name)
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
            valid_place=is_valid_place_name(place.name),
            is_restaurant_like=True,
            is_chain=chain_brand is not None,
            is_large_chain=chain_brand is not None,
            chain_brand=chain_brand,
            chain_scale="대형전국체인" if chain_brand else None,
            raw={},
        )
