from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from public_officer_pipeline.pipeline.batch import LoadBatch


class QualityGateResult(BaseModel):
    ok: bool
    severity: Literal["warn", "quarantine", "fail"]
    code: str
    message: str


def evaluate_batch(
    batch: LoadBatch,
    *,
    parsed_rows: int,
    require_storage_path: bool = False,
) -> list[QualityGateResult]:
    results: list[QualityGateResult] = []

    if parsed_rows > 0 and len(batch.visits) == 0:
        results.append(
            QualityGateResult(
                ok=False,
                severity="fail",
                code="zero_normalized_visits",
                message="parsed_rows is non-empty but no normalized visits were produced",
            ),
        )

    if batch.visits:
        avg_conf = sum(visit.confidence for visit in batch.visits) / len(batch.visits)
        if avg_conf < 0.8:
            results.append(
                QualityGateResult(
                    ok=False,
                    severity="fail",
                    code="low_average_confidence",
                    message=f"average confidence below threshold: {avg_conf:.3f} < 0.8",
                ),
            )

        if any(visit.confidence < 0.5 for visit in batch.visits):
            results.append(
                QualityGateResult(
                    ok=False,
                    severity="quarantine",
                    code="low_single_confidence",
                    message="at least one visit confidence below 0.5",
                ),
            )

    if len(batch.resolved_places) > 0:
        missing = sum(1 for place in batch.resolved_places.values() if place.latitude is None or place.longitude is None)
        if missing / len(batch.resolved_places) > 0.05:
            results.append(
                QualityGateResult(
                    ok=False,
                    severity="fail",
                    code="missing_coordinates",
                    message=(
                        "missing coordinate ratio exceeds threshold: "
                        f"{missing}/{len(batch.resolved_places)} > 0.05"
                    ),
                ),
            )

    if len(batch.visits) >= 5 and batch.resolved_places:
        if all(not place.matched for place in batch.resolved_places.values()):
            results.append(
                QualityGateResult(
                    ok=False,
                    severity="fail",
                    code="all_unmatched_places",
                    message="all resolved places are unmatched for a batch with 5 or more visits",
                ),
            )

    if not batch.storage_path and require_storage_path:
        results.append(
            QualityGateResult(
                ok=False,
                severity="fail",
                code="missing_storage_path",
                message="storage_path is required for non-dry-run runs",
            ),
        )

    if not results:
        results.append(
            QualityGateResult(
                ok=True,
                severity="warn",
                code="quality_pass",
                message="all quality gates passed",
            ),
        )

    return results
