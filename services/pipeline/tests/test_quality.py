from __future__ import annotations

from datetime import date
from uuid import uuid4

from public_officer_pipeline.pipeline.batch import LoadBatch, place_resolution_key
from public_officer_pipeline.pipeline.quality import evaluate_batch
from public_officer_pipeline.models import Agency, NormalizedVisit, PlaceRaw, ResolvedPlace


def _visit(*, confidence: float = 0.9, matched: bool = True, with_coordinates: bool = True) -> NormalizedVisit:
    return NormalizedVisit(
        agency_id=uuid4(),
        source_url="https://example.com/expense/1",
        source_title="title",
        source_published_at=date(2026, 5, 1),
        source_hash_sha256="abcdef1234",
        visit_date=date(2026, 5, 1),
        amount=10000,
        department_name="총무과",
        place_raw=PlaceRaw(name="테스트 식당", address_hint="서울 중구"),
        raw_excerpt="텍스트",
        confidence=confidence,
        latitude=37.5665 if with_coordinates else None,
        longitude=126.978 if with_coordinates else None,
    )


def _place(*, matched: bool = True, with_coordinates: bool = True) -> ResolvedPlace:
    return ResolvedPlace(
        kakao_place_id="kakao-id",
        natural_key="kakao-id",
        name="테스트 식당",
        road_address="서울 중구",
        road_address_part="서울 중구",
        latitude=37.5665 if with_coordinates else None,
        longitude=126.978 if with_coordinates else None,
        matched=matched,
    )


def _batch(*, visits: int = 1, with_coordinates: bool = True, all_unmatched: bool = False) -> LoadBatch:
    visits_data = [_visit(with_coordinates=with_coordinates) for _ in range(visits)]
    resolved_places = {
        place_resolution_key(visit.place_raw): _place(
            matched=not all_unmatched,
            with_coordinates=with_coordinates,
        )
        for visit in visits_data
    }
    return LoadBatch(
        agency=Agency(),
        source_url="https://example.com/expense/1",
        source_title="title",
        source_published_at=date(2026, 5, 1),
        source_hash_sha256="abcdef1234",
        source_file_kind="html",
        storage_path="r2://ok",
        visits=visits_data,
        resolved_places=resolved_places,
        extractor_model="llm",
    )


def test_evaluate_batch_flags_low_average_and_quarantine() -> None:
    batch = _batch(visits=1, with_coordinates=True)
    batch.visits[0].confidence = 0.4

    results = evaluate_batch(batch, parsed_rows=1)
    codes = {result.code for result in results}
    assert "low_average_confidence" in codes
    assert "low_single_confidence" in codes


def test_evaluate_batch_fails_when_no_normalized_visits_from_parsed_rows() -> None:
    batch = _batch(visits=0)
    result = evaluate_batch(batch, parsed_rows=1)
    assert result[0].code == "zero_normalized_visits"
    assert result[0].ok is False


def test_evaluate_batch_fails_when_all_unmatched_for_many_visits() -> None:
    batch = _batch(visits=5, all_unmatched=True)
    result = evaluate_batch(batch, parsed_rows=5)
    assert any(r.code == "all_unmatched_places" for r in result)
