# 07 — Acceptance Criteria

- **Status**: Planning (documentation only)
- **Date**: 2026-05-25

> Implementation note (2026-06-01): code now has the 138-agency taxonomy, `source-registry`,
> guarded batch `run-agencies`, and dry-run smoke coverage for selected 경기·인천 sources.
> Current registry status is **131 verified_in_code / 0 pending / 7 legal_hold**. Gate B's crawlable
> source discovery is complete for the capital area, but legal_hold entries remain excluded until a
> separate ADR/legal decision changes the 제1유형 policy. Gate C/D/E remain **not passed**
> because no staging/prod DB load has been approved or performed.

## 1. Purpose

Define the explicit "done" gates for each phase of v2, from this documentation stage through to deployment. Each gate must be fully satisfied before the next phase begins. Gates are sequential: docs → registry → dry-run → DB injection → deployment.

## 2. Gate A — v2 documentation complete

This planning stage is done when:

- [ ] All planning documents exist in `docs/v2/001_capital_area_expansion/` (README + 01–07), plus the buildable harness [08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md](08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md) and [ADR-011](../../adr/ADR-011-agency-taxonomy-model.md).
- [ ] Scope is unambiguous: Seoul 52 unchanged, Gyeonggi 64 new, Incheon 22 new, **total 138** ([01_SCOPE.md](01_SCOPE.md)).
- [ ] The fact that **Seoul is already fully wired (0 `adapter_required`)** is reflected, so v2 is framed as purely additive (86 new agencies) ([02_SOURCE_REGISTRY_PLAN.md](02_SOURCE_REGISTRY_PLAN.md) §2).
- [ ] Every document distinguishes **[FACT] / [ASSUMPTION] / [TODO]** and invents no real source URLs.
- [ ] v1 forbidden features (restaurant/place comments, ratings, reviews, and any data-rollout expansion of community/reactions beyond ADR-012) are reaffirmed as forbidden ([06_LEGAL_AND_RISK_PLAN.md](06_LEGAL_AND_RISK_PLAN.md) §3).
- [ ] [docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) is named as the final authority and the governor/county-head masking enumeration is flagged as a prerequisite edit.
- [ ] [RESOLVED] ADR-011 taxonomy (`gov_tier`, `branch`, `jurisdiction_type`) is adopted as the contract basis for province/metro/county agencies before gating to Gate D.
- [ ] No code, DB, deploy, or crawl was performed.

## 3. Gate B — source registry complete

Before any crawl (per [02_SOURCE_REGISTRY_PLAN.md](02_SOURCE_REGISTRY_PLAN.md) §7):

- [ ] All 86 new agencies have a registry entry (province/metro + 시·군·구, office + council).
- [ ] Every crawlable entry has a verified, non-`TODO` `source_url`, `document_format`, `update_frequency`, `crawl_difficulty`, with `verified_at` + `verified_by` stamped.
- [ ] Each source's authority and license (공공누리 제1유형 or equivalent) is individually confirmed and its attribution string captured.
- [ ] Agencies with no online disclosure are explicitly marked in `notes` (not left ambiguous).
- [ ] Name-collision agencies (중구/동구/서구) carry unambiguous `region` keys.
- [ ] A verified-vs-pending summary exists so batches can be planned.

## 4. Gate C — dry-run complete (per batch)

Before promotion of a batch (per [03_BACKFILL_AND_PIPELINE_PLAN.md](03_BACKFILL_AND_PIPELINE_PLAN.md) §8, [04_DATA_QUALITY_PLAN.md](04_DATA_QUALITY_PLAN.md) §9):

- [ ] Batch loaded into an isolated **Neon staging branch** only (no production write).
- [ ] **Masking SQL checks return 0** (hard legal block), plus a clean 30-row manual eyeball.
- [ ] Parse success ≥ target, or sub-threshold agencies explicitly quarantined.
- [ ] Coordinate completeness < 5% missing; placeId match rate recorded.
- [ ] Entity-resolution dedupe reviewed; no unresolved bad merges/splits; no cross-region merges.
- [ ] Grade distribution within tolerance per partition; small-partition fallback verified.
- [ ] Regional sample ≥ 95% field match against source documents.
- [ ] All §8 risk cases ([04_DATA_QUALITY_PLAN.md](04_DATA_QUALITY_PLAN.md)) cleared or consciously waived with a recorded reason.

## 5. Gate D — production DB injection allowed (per batch)

Before writing a batch to production (per [05_DB_ROLLOUT_PLAN.md](05_DB_ROLLOUT_PLAN.md) §2):

- [ ] Gate B (registry) and Gate C (dry-run) passed for this batch.
- [ ] Agency-taxonomy migration ([ADR-011](../../adr/ADR-011-agency-taxonomy-model.md) via [08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md](08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md)) is merged, tests green (52/64/22/138), and `DATA_MODEL.md` synced.
- [ ] Any schema migration applied to staging first, reviewed, proven reversible.
- [ ] Production backup confirmed: Neon PITR available + current `pg_dump`.
- [ ] Explicit `agency_id` list for the batch recorded (enables targeted rollback).
- [ ] Load is verified **additive** (no Seoul rows modified/deleted).
- [ ] Rollback path confirmed **before** the write.
- [ ] Operator sign-off recorded with date and referenced gate results.

Batches are injected in order: **1) Incheon → 2) Gyeonggi 5–10 sample → 3) Gyeonggi full → 4) capital-area unified grade recompute** ([05_DB_ROLLOUT_PLAN.md](05_DB_ROLLOUT_PLAN.md) §4).

## 6. Gate E — deployment allowed

Before the expanded coverage is exposed to users:

- [ ] Production data for the promoted batches is loaded and grades recomputed; Seoul partitions confirmed unchanged.
- [ ] API serves the new regions correctly (bbox/region/agency-type queries return new rows; API/front-end must accept `gov_tier`, `branch`, `jurisdiction_type` filtering and values).
- [ ] `road_address_part` for new regions follows `"<시도> <시·군·구>"` so partitions group correctly.
- [ ] Front-end changes (filters, default extent) — if part of the deploy — tested in a browser across the golden path and key edge cases; if not yet built, the limitation is stated explicitly (new rows simply sit outside Seoul's default viewport, UI not broken).
- [ ] **Attribution preserved**: the line **"공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외"** is present in **footer, OpenAPI (`/openapi.json`), and `llms.txt`/`llms-full.txt`**, with the "외 N개 기관" count updated and new sources listed on `/legal`.
- [ ] Legal/privacy docs reflect the extended elected-official set ([06_LEGAL_AND_RISK_PLAN.md](06_LEGAL_AND_RISK_PLAN.md) §4) and pass the v1 legal-page checks ([docs/TEST_PLAN.md](../../TEST_PLAN.md)).
- [ ] Takedown SLA (72h) and operator identity intact across all regions.

## 7. Attribution invariant (must hold at every gate from D onward) **[FACT]**

The attribution string **"공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외"** must remain visible in **footer / OpenAPI / llms.txt** at all times. v2 only updates the trailing "외 N개 기관" count and the `/legal` per-source listing — it never removes or weakens the attribution. A change that drops this attribution is a **merge block** ([docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) §"위반 시 머지 금지").

## 8. Sequencing summary

```
Gate A (docs)            ← this stage ends here
   ↓
Gate B (registry verified)
   ↓
Gate C (dry-run on staging, per batch)
   ↓
Gate D (production injection, per batch, ordered: Incheon → GG sample → GG full → recompute)
   ↓
Gate E (deployment to users)
```

Each gate is a hard stop. No gate may be skipped, and any failure routes back to the responsible document's procedure rather than forcing the gate.
