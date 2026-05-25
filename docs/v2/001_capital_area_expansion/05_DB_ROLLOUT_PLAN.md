# 05 — DB Rollout Plan

- **Status**: Planning (documentation only)
- **Date**: 2026-05-25

## 1. Purpose

Define the controlled path from a passing staging dry-run to live production data: pre-injection checklist, promotion criteria, batched rollout, rollback/recompute strategy, and compatibility with the existing API and front-end.

> Nothing here is executed in this stage. This is the procedure to follow when each batch is later approved.

## 2. Pre-injection checklist (per batch)

Before any write to the production Neon database, confirm:

- [ ] **Source registry** for the batch's agencies is verified (non-`TODO` `source_url`, `document_format`, `crawl_difficulty`; `verified_at` stamped) — [02_SOURCE_REGISTRY_PLAN.md](02_SOURCE_REGISTRY_PLAN.md) §7.
- [ ] **Dry-run on staging** completed for exactly this batch — [03_BACKFILL_AND_PIPELINE_PLAN.md](03_BACKFILL_AND_PIPELINE_PLAN.md) §8.
- [ ] **Quality gates passed** on staging — all of [04_DATA_QUALITY_PLAN.md](04_DATA_QUALITY_PLAN.md) §9.
- [ ] **Masking SQL = 0** on staging (hard legal block) — [04_DATA_QUALITY_PLAN.md](04_DATA_QUALITY_PLAN.md) §3, authority [docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md).
- [ ] **Taxonomy contract** (`gov_tier`, `branch`, `jurisdiction_type`) is confirmed for province/metro/county representation — [01_SCOPE.md](01_SCOPE.md) §6.
- [ ] **Schema migration (if any) applied to staging first**, reviewed, and proven reversible.
- [ ] **Production backup point** confirmed: Neon Point-in-Time Restore available + the weekly `pg_dump` is current ([docs/RISK_MITIGATION.md](../../RISK_MITIGATION.md) §"데이터 백업 정책").
- [ ] **Attribution string updated**: footer / `/legal` / `llms.txt` / OpenAPI reflect the expanded "외 N개 기관" count (see §8).
- [ ] **Operator sign-off** recorded with date and the gate results referenced.

## 3. Staging → production promotion criteria

A batch is promoted only when **all** of:

1. Every item in §2 is checked.
2. The staging branch's data for the batch is byte-for-byte the result of the same idempotent pipeline that will run against production (same code, same `source_pattern`, same model routing) — so production load reproduces staging, not something new.
3. The promotion is **additive**: it inserts new agencies' `place_visits`/`places`/`sources` and does not modify or delete Seoul rows.
4. A rollback path (§6) is confirmed before, not after, the write.

Promotion itself is the normal idempotent pipeline run targeting `DATABASE_URL` (production) instead of the staging branch — there is no separate "copy from staging" step; staging proves the run, production repeats it.

## 4. Batched rollout plan

Aligned with the crawl batch order in [03_BACKFILL_AND_PIPELINE_PLAN.md](03_BACKFILL_AND_PIPELINE_PLAN.md) §4:

| Batch | Content | Agencies | Promotion gate |
|---|---|---|---|
| **1 — Incheon** | Incheon metro office + council + 10 군·구 offices + 10 군·구 councils | 22 | Full §2 checklist; this batch also validates the new `gov_tier/branch/jurisdiction_type` handling and name-collision handling for the first time. |
| **2 — Gyeonggi sample** | 5–10 representative 시·군 (≥1 특례시, ≥1 mid city, ≥1 군), office + council each | ~10–20 | Full §2 checklist; format-diversity sign-off (HWP/scanned PDF proven). |
| **3 — Gyeonggi full** | Remaining Gyeonggi agencies up to 64 total | remainder | Full §2 checklist per sub-group; may itself be split into smaller waves if a format proves troublesome. |
| **4 — Capital-area unified grade recompute** | `REFRESH MATERIALIZED VIEW CONCURRENTLY place_grade_v1` over all regions | all | Grade-distribution sanity per partition ([04_DATA_QUALITY_PLAN.md](04_DATA_QUALITY_PLAN.md) §6); confirm Seoul partitions unchanged. |

Notes:

- Each batch is independently promotable and independently reversible.
- Batch 4 is a **recompute, not a reload**. Because grades are partitioned by `road_address_part` ([ADR-004](../../adr/ADR-004-ranking-formula.md)), adding new 시·군·구 partitions does **not** change Seoul's percentile cutoffs — Seoul grades are mathematically isolated. This is the key compatibility guarantee for keeping Seoul stable.

## 5. Grade recompute behavior

**[FACT]** `place_grade_v1` percentiles are computed `PARTITION BY road_address_part` ([docs/DATA_MODEL.md](../../DATA_MODEL.md), [docs/ALGORITHM.md](../../ALGORITHM.md)). Therefore:

- New regions add new partitions; existing Seoul partitions' inputs are untouched ⇒ Seoul grades do not move because of v2 data.
- The recompute is the existing daily `REFRESH MATERIALIZED VIEW CONCURRENTLY` via `/api/cron/recompute-grades` — no new mechanism.
- Small new partitions (< 30 places) use the documented fallback distribution; verify it engages (see [04_DATA_QUALITY_PLAN.md](04_DATA_QUALITY_PLAN.md) §6).

## 6. Rollback / recompute strategy

Because every load is additive and idempotent, rollback is scoped to a batch's agencies:

| Situation | Rollback action |
|---|---|
| Bad batch detected post-promotion | Delete the batch's rows by `agency_id` set (the new agencies are disjoint from Seoul), then re-`REFRESH` grades. Seoul untouched. |
| Schema migration reg/ problem | Neon Point-in-Time Restore to the pre-migration point on a branch; validate; cut over. Production PITR window per plan ([docs/DATA_MODEL.md](../../DATA_MODEL.md) §"백업·복원"). |
| Masking issue slipped to prod | Immediate: hide affected rows (`hidden_at`), then delete + reload corrected. Treat as a [docs/RISK_MITIGATION.md](../../RISK_MITIGATION.md) incident. |
| Grade anomaly only | Re-`REFRESH` after fixing inputs; grades are derived, so no data loss — recompute is cheap and safe. |

Pre-promotion, always have: (a) PITR available, (b) current `pg_dump`, (c) the explicit `agency_id` list for the batch so a targeted delete is trivial.

## 7. API / front-end compatibility

**[FACT]** v1 reads go through `*_public` views and Vercel API Routes ([docs/PUBLIC_API.md](../../PUBLIC_API.md), [docs/ARCHITECTURE.md](../../ARCHITECTURE.md)). Compatibility considerations:

- **Additive data is transparent to the API**: `/api/v1/places`, `/places/{id}`, `/places/{id}/visits`, `/api/v1/agencies`, `/agencies/{id}` return whatever rows match the query (bbox/grade/region). New regions simply appear when queried within their bounding boxes. No endpoint contract change is required to *serve* the data.
- **Filters / map bounds**: the front-end's region/agency-type filters and the map's initial Seoul-centered view ([docs/UI_UX.md](../../UI_UX.md)) currently assume Seoul. To *surface* Gyeonggi/Incheon to users, the front-end will need filter options and a wider default/extent — **but that is a front-end change tracked separately and is not part of this doc-only stage.** Loading the data does not break the existing Seoul UI; the new rows are just outside Seoul's default viewport until the UI is extended.
- **`agencies` taxonomy**: if the taxonomy is applied for province/metro/county ([01_SCOPE.md](01_SCOPE.md) §6), any API field exposing `gov_tier`, `branch`, or `jurisdiction_type` and any front-end filter keyed on those dimensions must accept the new values. This is the one place an additive data load could surface a contract gap; it is gated in §2.
- **`road_address_part` format**: new partitions must follow the same `"<시도> <시·군·구>"` convention the algorithm partitions on, so the recompute groups correctly. Confirm the geocoder produces this format for Gyeonggi/Incheon (e.g. `"경기 수원시"`, `"인천 강화군"`), per [docs/PIPELINE.md](../../PIPELINE.md) §"road_address_part 추출".

## 8. Attribution update (must not break) **[FACT]**

[docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) and [AGENTS.md](../../../AGENTS.md) require the public-domain attribution in footer / `/legal` / `llms.txt` / OpenAPI. On rollout:

- Keep the base line **"공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외"**.
- Update the "외 N개 기관" count and add the new source agencies (Gyeonggi/Incheon portals/boards) to the `/legal` per-source listing as they are verified.
- This is a **carry-over obligation, not a redesign** — see [07_ACCEPTANCE_CRITERIA.md](07_ACCEPTANCE_CRITERIA.md).

## 9. What this stage does NOT do

- Does not write to production.
- Does not create branches, run migrations, or refresh grades.
- Does not change the API or front-end.
- It only defines the gates and the reversible procedure for when each batch is approved.
