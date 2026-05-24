from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


SEOUL_CITY_HALL_AGENCY_ID = UUID("00000000-0000-0000-0000-000000000001")


class AgencyKind(StrEnum):
    CITY_HALL = "city_hall"
    CITY_COUNCIL = "city_council"
    GU_OFFICE = "gu_office"
    GU_COUNCIL = "gu_council"


class Agency(BaseModel):
    id: UUID = SEOUL_CITY_HALL_AGENCY_ID
    name: str = "서울특별시청"
    short_name: str = "서울시청"
    kind: AgencyKind = AgencyKind.CITY_HALL
    parent_region: str = "서울특별시"
    sub_region: str | None = None
    homepage: str = "https://opengov.seoul.go.kr/expense/list"
    source_pattern: dict[str, Any] = Field(
        default_factory=lambda: {"adapter": "seoul_opengov", "searchKeyword": "서울시본청"}
    )


class PostRef(BaseModel):
    agency_id: UUID
    url: str
    title: str
    published_at: date | None = None
    department_name: str | None = None
    file_kind: str = "html"


class PostDetail(PostRef):
    html: str
    content_bytes: bytes | None = None
    fetched_at: datetime
    hash_sha256: str


class ParsedExpenseRow(BaseModel):
    department_name: str
    used_at: datetime
    place_text: str
    purpose: str | None = None
    amount: int
    user_text: str | None = None
    payment_method: str | None = None
    expense_category: str | None = None
    raw_excerpt: str


class PlaceRaw(BaseModel):
    name: str
    address_hint: str | None = None


class NormalizedVisit(BaseModel):
    agency_id: UUID
    source_url: str
    source_title: str
    source_published_at: date | None = None
    source_hash_sha256: str
    visit_date: date
    amount: int
    party_size: int | None = None
    purpose: str | None = None
    department_name: str | None = None
    rank_label: str | None = None
    representative: str | None = None
    payment_method: str | None = None
    expense_category: str | None = None
    place_raw: PlaceRaw
    raw_excerpt: str
    confidence: float = Field(ge=0, le=1)


class ResolvedPlace(BaseModel):
    kakao_place_id: str | None
    natural_key: str
    name: str
    road_address: str | None = None
    jibun_address: str | None = None
    road_address_part: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    category: str | None = None
    phone: str | None = None
    matched: bool
    raw: dict[str, Any] = Field(default_factory=dict)


class PipelineStats(BaseModel):
    posts_seen: int = 0
    posts_fetched: int = 0
    parsed_rows: int = 0
    normalized_visits: int = 0
    places_seen: int = 0
    kakao_matched_places: int = 0
    loaded_sources: int = 0
    loaded_places: int = 0
    loaded_visits: int = 0

    @property
    def kakao_match_rate(self) -> float:
        if self.places_seen == 0:
            return 0.0
        return self.kakao_matched_places / self.places_seen


class PipelineConfigError(RuntimeError):
    pass


class LoaderResult(BaseModel):
    source_id: UUID
    place_id_by_natural_key: dict[str, UUID]
    visit_ids: list[UUID]
