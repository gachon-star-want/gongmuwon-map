from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from public_officer_pipeline.models import Agency, NormalizedVisit, PlaceRaw, ResolvedPlace


def place_resolution_key(place_raw: PlaceRaw) -> str:
    return place_raw.model_dump_json()


class LoadBatch(BaseModel):
    agency: Agency
    source_url: str
    source_title: str
    source_published_at: date | None
    source_hash_sha256: str
    source_file_kind: str
    storage_path: str | None = None
    visits: list[NormalizedVisit]
    resolved_places: dict[str, ResolvedPlace]
    extractor_model: str
