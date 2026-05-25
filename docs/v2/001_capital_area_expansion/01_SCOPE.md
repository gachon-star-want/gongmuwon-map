# 01 — Scope

- **Status**: Planning (documentation only)
- **Date**: 2026-05-25

## 1. Purpose of this document

Define the exact set of agencies in scope for v2, estimate the total agency count, and state explicitly what is included, excluded, and carried over unchanged from v1.

## 2. Seoul — unchanged (52 agencies)

**[FACT]** v1 covers 52 Seoul agencies: Seoul City Hall (1) + Seoul Metropolitan Council (1) + 25 district (자치구) offices + 25 district councils. This is asserted directly in code (`services/pipeline/src/public_officer_pipeline/agencies.py`: `assert len(SEOUL_AGENCIES) == 52`) and in [docs/PRD.md](../../PRD.md).

**[FACT]** Seoul is already **fully wired at the source/adapter level**: all 52 agencies have a concrete crawler adapter and **0 remain in `adapter_required` state** (verified 2026-05-25). Real crawler/extractor code for Seoul already exists in the repo. In other words, Seoul is essentially complete as the working reference implementation, and v2 is **purely additive** — it builds the 86 new agencies on top of a finished Seoul, copying Seoul's proven patterns. See [02_SOURCE_REGISTRY_PLAN.md](02_SOURCE_REGISTRY_PLAN.md) §2 for the adapter breakdown.

v2 therefore **keeps all 52 Seoul agencies exactly as they are**. No re-scoping, no re-keying, no policy change, and **no new source-registry work** for Seoul. Seoul data and its grades remain live throughout the v2 rollout; v2 does not pause, re-crawl, or rebuild Seoul (the only Seoul-touching step is the final capital-area-wide grade recompute in [05_DB_ROLLOUT_PLAN.md](05_DB_ROLLOUT_PLAN.md), which adds new percentile partitions without altering Seoul's own partitions).

## 3. Gyeonggi-do — new

**[FACT]** Gyeonggi-do is composed of 31 시·군 (cities and counties): 28 cities (시) + 3 counties (군).

Target agencies for Gyeonggi:

| Group | Count | Notes |
|---|---|---|
| Provincial office (경기도청) | 1 | `regional/admin`-equivalent at the provincial level — see taxonomy note below. |
| Provincial council (경기도의회) | 1 | `regional/council`-equivalent. |
| 시/군 offices (시청·군청) | 31 | One per 시·군. |
| 시/군 councils (시의회·군의회) | 31 | One per 시·군. |
| **Subtotal** | **64** | |

### 3.1 Gyeonggi 31 시·군 list **[FACT]**

Cities (28): 수원시, 성남시, 의정부시, 안양시, 부천시, 광명시, 평택시, 동두천시, 안산시, 고양시, 과천시, 구리시, 남양주시, 오산시, 시흥시, 군포시, 의왕시, 하남시, 용인시, 파주시, 이천시, 안성시, 김포시, 화성시, 광주시, 양주시, 포천시, 여주시.

Counties (3): 연천군, 가평군, 양평군.

> Note: 수원·성남·고양·용인 are 특례시 (special-case cities) and several large cities have 구 (non-autonomous districts, 일반구). **[ASSUMPTION]** Business-expense disclosure is published at the 시 level (and at the 군 level), not separately per 일반구, so we treat each 시·군 as one office + one council. This must be confirmed during source verification ([02_SOURCE_REGISTRY_PLAN.md](02_SOURCE_REGISTRY_PLAN.md)); if any city publishes per-일반구, that becomes a registry TODO, not an automatic agency split.

## 4. Incheon — new

**[FACT]** Incheon is composed of 10 군·구: 8 districts (구) + 2 counties (군).

Target agencies for Incheon:

| Group | Count | Notes |
|---|---|---|
| Metropolitan office (인천광역시청) | 1 | `regional/admin`-equivalent. |
| Metropolitan council (인천광역시의회) | 1 | `regional/council`-equivalent. |
| District/county offices (구청·군청) | 10 | One per 군·구. |
| District/county councils (구의회·군의회) | 10 | One per 군·구. |
| **Subtotal** | **22** | |

### 4.1 Incheon 10 군·구 list **[FACT]**

Districts (8): 중구, 동구, 미추홀구, 연수구, 남동구, 부평구, 계양구, 서구.

Counties (2): 강화군, 옹진군.

## 5. Total target agency count

| Region | Agencies |
|---|---|
| Seoul (unchanged) | 52 |
| Gyeonggi (new) | 64 |
| Incheon (new) | 22 |
| **Total** | **138** |

**[FACT]** v2 adds **86 new agencies** (64 Gyeonggi + 22 Incheon) on top of the 52 existing Seoul agencies, for a capital-area total of **138**.

## 6. Agency taxonomy resolution

**[FACT]** The v1 schema used `agencies.kind` with values `'city_hall' | 'city_council' | 'gu_office' | 'gu_council'`.

**[RESOLVED by [ADR-011](../../adr/ADR-011-agency-taxonomy-model.md)]** Gyeonggi (a 도, province) and Incheon (a 광역시, metropolitan city) do not map cleanly onto Seoul's 특별시 + 자치구 model, so the single `kind` enum is replaced by a two-axis model plus a descriptive type:

- `gov_tier`: `regional` (광역자치단체) | `basic` (기초자치단체).
- `branch`: `admin` (집행부/청) | `council` (의회).
- `jurisdiction_type`: `special_city` | `metro_city` | `province` | `autonomous_gu` | `si` | `gun`.

Examples: 경기도청 = `(regional, admin, province)`; 수원시청 = `(basic, admin, si)`; 연천군청 = `(basic, admin, gun)`; 인천광역시청 = `(regional, admin, metro_city)`; 인천 중구청 = `(basic, admin, autonomous_gu)`. Seoul rows map losslessly (old `city_hall`→`(regional, admin)`, `gu_office`→`(basic, admin)`, etc.) and keep identical `agency.id` values.

The exact, file-by-file implementation (schema migration + new agencies as `adapter_required` stubs) is specified in [08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md](08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md). This is the one schema change v2 introduces; it is gated as a prerequisite for the data-loading stage in [07_ACCEPTANCE_CRITERIA.md](07_ACCEPTANCE_CRITERIA.md).

## 7. What v2 includes

- All 86 new agencies' business-expense (업무추진비) disclosures, same data fields as v1.
- Same data window policy as v1 (rolling 12 months for grading + 24-month backfill retained) — see [03_BACKFILL_AND_PIPELINE_PLAN.md](03_BACKFILL_AND_PIPELINE_PLAN.md).
- Same grade algorithm, recomputed so that percentile cutoffs are partitioned by `road_address_part` (each new 시·군·구 becomes its own partition) — see §9.
- Map, filters, detail panel, and public API extended to render the new regions (front-end/API changes are out of scope for *this documentation stage* but are accounted for in the rollout plan).

## 8. What v2 excludes (intentional non-goals)

Carried over from v1 [docs/PRD.md](../../PRD.md) "what's NOT in v1", and explicitly reaffirmed for v2:

- ❌ User comments, ratings, reviews, likes, or any community feature — defamation risk; **forbidden** ([docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) §"merge-block policy").
- ❌ Automatic food-category classification as a grade input.
- ❌ Forced sign-up / accounts.
- ❌ Native mobile app.

v2-specific exclusions:

- ❌ Regions beyond the capital area (충청/경상/전라/강원/제주 stay on the v3+ roadmap).
- ❌ Any change to the v1 grade *formula* itself (only its data scope and partitions grow). A formula change would require a new ADR superseding [ADR-004](../../adr/ADR-004-ranking-formula.md).
- ❌ Per-일반구 agency splitting unless source verification proves separate publication (see §3.1).

## 9. v1 policies carried over unchanged

| Area | v1 decision | v2 status |
|---|---|---|
| Data source strategy | Official disclosure portals + agency boards, attachments → text → LLM ([ADR-001](../../adr/ADR-001-data-source-strategy.md)) | **Kept.** Extended to new portals/boards. |
| Extraction | All-LLM general extraction, multi-provider routing ([ADR-002](../../adr/ADR-002-llm-extraction.md), ADR-009) | **Kept.** No per-site hand-coded parsers required for new agencies. |
| Entity resolution | Kakao placeId + (normalized name + geohash) fallback ([ADR-003](../../adr/ADR-003-entity-resolution.md)) | **Kept.** |
| Grade formula | `visit_count_12m × log10(unique_dept + 1)`, per-region percentile cutoff ([ADR-004](../../adr/ADR-004-ranking-formula.md)) | **Kept.** New regions added as new partitions. |
| Map provider | Kakao Map JS + Kakao Local ([ADR-005](../../adr/ADR-005-map-provider.md)) | **Kept.** |
| Stack | Vite/React/Mantine + Neon + R2 + Vercel ([ADR-010](../../adr/ADR-010-database-stack-migration.md)) | **Kept.** |
| Masking policy | Elected = name+rank; appointed = rank+dept, name masked; rank-5-and-below = dept + "외 N명"; masking at load time ([docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md)) | **Kept, non-negotiable.** |
| Attribution | Footer/OpenAPI/llms.txt "공공누리 제1유형 · 출처: …" | **Kept**; "외 N개 기관" count updated for expanded coverage. |
| Takedown SLA | Notice-and-takedown, immediate hide, 72h review | **Kept.** |

## 10. Out-of-scope-for-this-document items (handled elsewhere)

- Exact source URLs per agency → [02_SOURCE_REGISTRY_PLAN.md](02_SOURCE_REGISTRY_PLAN.md) (mostly TODO until verified).
- Crawl/extraction batch ordering → [03_BACKFILL_AND_PIPELINE_PLAN.md](03_BACKFILL_AND_PIPELINE_PLAN.md).
- Quality gates → [04_DATA_QUALITY_PLAN.md](04_DATA_QUALITY_PLAN.md).
- Production rollout/rollback → [05_DB_ROLLOUT_PLAN.md](05_DB_ROLLOUT_PLAN.md).
