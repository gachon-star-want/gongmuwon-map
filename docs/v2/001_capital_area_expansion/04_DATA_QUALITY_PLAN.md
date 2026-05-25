# 04 — Data Quality Plan

- **Status**: Planning (documentation only)
- **Date**: 2026-05-25

## 1. Purpose

Define the quality gates a v2 batch must pass on the staging branch ([03_BACKFILL_AND_PIPELINE_PLAN.md](03_BACKFILL_AND_PIPELINE_PLAN.md) §8) before promotion to production. These reuse and extend v1's checks ([docs/TEST_PLAN.md](../../TEST_PLAN.md), [docs/PIPELINE.md](../../PIPELINE.md) §"데이터 품질 검증").

> Targets below marked **[ASSUMPTION]** are proposed thresholds inherited from v1's intent; the operator confirms or tightens them during the Incheon dry-run.

## 2. Parse success rate

- **Metric**: % of fetched documents that yield ≥ 1 valid normalized visit row (vs. landing in the extraction-failure queue).
- **Target [ASSUMPTION]**: ≥ 90% per agency for the batch to promote; agencies below threshold are quarantined and reviewed, not blindly loaded.
- **Watch**: HWP/HWPX and scanned-PDF agencies (expected weak spots in Gyeonggi/Incheon, see [03_BACKFILL_AND_PIPELINE_PLAN.md](03_BACKFILL_AND_PIPELINE_PLAN.md) §5). Track scanned-vs-text PDF share.
- **Confidence distribution**: monitor mean / p10 / p90 of `extractor_confidence`. Rows with confidence < 0.8 trigger model escalation (per ADR-009) before they count toward success.

## 3. Personal-data masking verification (security-critical)

This is the highest-priority gate. [docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) is the final authority; a batch that fails masking is **blocked**, no exceptions.

Reuse the v1 SQL checks ([docs/TEST_PLAN.md](../../TEST_PLAN.md)) run against the **staging branch**:

```sql
-- 1. representative must only hold elected-official ranks
SELECT COUNT(*) FROM place_visits
WHERE representative IS NOT NULL
  AND rank_label NOT IN ('시장','구청장','시의원','구의원',
                         '도지사','군수','도의원');  -- v2-extended set
-- expect: 0

-- 2. no identifiable Korean name leaking into department_name
SELECT COUNT(*) FROM place_visits
WHERE department_name ~ '^[가-힣]{2,4} (외|국장|과장|팀장|군수|시장)';
-- expect: 0
```

**v2-specific extension [FACT-driven]**: the elected-official allowlist must add the Gyeonggi/Incheon roles — **도지사 (governor)**, **시장·군수·구청장**, **광역의원(도의원/광역시의원)**, **기초의원(시·군·구의원)**. The exact final list must match [docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md); if that document needs the roles enumerated for the new regions, that update is tracked in [06_LEGAL_AND_RISK_PLAN.md](06_LEGAL_AND_RISK_PLAN.md) (and may need a doc edit before promotion).

- **Target**: query (1) and (2) both return **0** on staging. Non-zero ⇒ hard block.
- **Manual spot-check**: in addition to SQL, sample 30 rows per batch and eyeball for any name leakage the regex missed.

## 4. Kakao placeId match rate

- **Metric**: % of resolved places that matched a Kakao `placeId` (vs. falling back to `natural_key`).
- **Target [ASSUMPTION]**: comparable to Seoul's observed rate (record Seoul's actual rate as the baseline during the dry-run rather than guessing a number).
- **Coordinate completeness**: % of places with non-NULL lat/lng must stay **< 5% missing** (v1 target, [docs/PIPELINE.md](../../PIPELINE.md)).
- **Watch**: Gyeonggi/Incheon restaurant names may be less represented in Kakao Local than central Seoul; a lower match rate is acceptable as long as natural_key fallback keeps coordinate completeness within target. Cache behavior (7-day) per [ADR-003](../../adr/ADR-003-entity-resolution.md) stays.

## 5. Duplicate-restaurant entity resolution

- **Metric**: detect places that should be one but were split (same physical restaurant under name variants) and places wrongly merged.
- **Checks**:
  - Count of `natural_key` places within a small geohash radius that share a normalized name → candidate splits to review.
  - Any single `kakao_place_id` spanning unexpectedly distant coordinates → candidate bad merge.
- **Cross-region collision**: ensure no place is merged across regions purely by name (e.g. a "본가" in 인천 중구 vs 서울 중구). Entity resolution keys on coordinates + placeId, so this should not happen, but it is explicitly checked during the dry-run.
- **Target [ASSUMPTION]**: duplicate/split rate on the sampled set within the same tolerance accepted for Seoul; material regressions block promotion and route to the merge-review queue (operator tool is v1.1).

## 6. Grade distribution sanity (outlier detection)

After the staging grade recompute, per new partition (`road_address_part` = each 시·군·구):

```sql
SELECT road_address_part, grade, COUNT(*)
FROM place_grade_v1 g JOIN places p ON p.id = g.place_id
GROUP BY road_address_part, grade
ORDER BY road_address_part, grade;
```

- **Expected shape [FACT, from ADR-004/ALGORITHM]**: ★★★ ≈ 10±2%, ★★ ≈ 20±5%, ★ ≈ 30±5% within each partition.
- **Small-partition fallback [FACT]**: a 시·군·구 with < 30 places uses the broader fallback distribution (per [ADR-004](../../adr/ADR-004-ranking-formula.md) / [docs/ALGORITHM.md](../../ALGORITHM.md)). Many rural 군 will be small early on — expected, not an error; verify the fallback path actually engages.
- **Outliers to flag**: a partition where ★★★ is wildly off (e.g. 0% or 40%), or a single restaurant with an implausibly high `visit_count_12m` (possible double-load or extraction error).

## 7. Regional sampling standard

For each batch, manual 1:1 verification against the original document (extends [docs/TEST_PLAN.md](../../TEST_PLAN.md) "30-row sample"):

- **Incheon batch**: sample **≥ 30 rows** spread across all 22 agencies (at least 1 per agency where data exists).
- **Gyeonggi sample batch**: **≥ 30 rows** across the 5–10 chosen 시·군, deliberately including at least one 특례시, one mid city, and one 군.
- **Gyeonggi full batch**: **≥ 50 rows** across the remaining agencies, weighted toward agencies with new/unusual formats (HWP, scanned PDF).
- **Field match target [FACT, v1]**: restaurant name / amount / date / department ≥ **95%** match against source.

## 8. Risk cases requiring manual review

Cases that must not auto-promote and instead go to a human:

| Case | Why | Action |
|---|---|---|
| HWP/HWPX parse below threshold | New format reliance in Gyeonggi/Incheon | Inspect samples; fix extractor path or quarantine agency. |
| Scanned-PDF-heavy agency | Vision extraction error-prone | Higher sampling ratio; confirm masking on vision output. |
| Masking SQL returns non-zero | Legal hard-block | Stop batch; fix prompt/validator; re-run. |
| Name collision across regions | 중구/동구/서구 duplication | Verify region keys; confirm no cross-region merge. |
| Per-일반구 publication discovered | Scope assumption ([01_SCOPE.md](01_SCOPE.md) §3.1) wrong | Decide agency split via registry update before loading. |
| Partition grade shape far off target | Possible double-load / extraction error | Inspect top-`visit_count` rows; check idempotency key. |
| Taxonomy migration gap | Schema change needed if v1 `kind` is assumed | **Resolved by ADR-011** (`gov_tier`, `branch`, `jurisdiction_type`). Keep this row for historical traceability only. |

## 9. Gate summary → promotion

A batch is promotable only when, on staging:

1. Parse success ≥ target (or sub-threshold agencies explicitly quarantined).
2. Masking SQL checks (1)(2) = **0**, plus clean 30-row eyeball.
3. Coordinate completeness < 5% missing.
4. placeId match rate recorded and not anomalously low without explanation.
5. Dedupe checks reviewed; no unresolved bad merges/splits.
6. Grade distribution within tolerance per partition (small-partition fallback verified).
7. Regional sample ≥ 95% field match.
8. All §8 risk cases either cleared or consciously waived by the operator with a recorded reason.

Promotion mechanics and rollback are in [05_DB_ROLLOUT_PLAN.md](05_DB_ROLLOUT_PLAN.md).
