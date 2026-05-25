# v2 — Capital Area Expansion (Seoul + Gyeonggi + Incheon)

- **Status**: Planning (documentation only)
- **Date**: 2026-05-25
- **Scope owner**: 이원영/WonYoungLee (operator)

## What this is

This folder holds the **planning documents** for the v2 expansion of 공무원맵 (Public Officer Map) from Seoul-only coverage to the full Seoul Capital Area (수도권): **Seoul + Gyeonggi-do + Incheon**.

> **This stage is planning documents ONLY.** No code changes, no production DB writes, no deployment, no crawl execution happen as part of this stage. Every document here is a plan to be reviewed and approved before any operational step begins.

These documents describe *what we intend to do* and *how we will verify it before touching production*. They do not themselves perform any of those actions.

## Goal

- Keep the existing Seoul coverage (52 agencies) exactly as-is.
- Add Gyeonggi-do: provincial office, provincial council, 31 city/county offices, 31 city/county councils.
- Add Incheon: metropolitan office, metropolitan council, 10 district/county offices, 10 district/county councils.
- Do all of this **without breaking any v1 policy** — no comments, ratings, reviews, likes, or community features; no exposure of masked personal identities; no loss of the public-domain (공공누리 제1유형) attribution.

## Non-goals for this stage

- ❌ Writing or modifying pipeline/web/API code.
- ❌ Injecting any data into the production database.
- ❌ Running crawlers against any real agency website.
- ❌ Deploying anything.
- ❌ Inventing real source URLs we have not verified (unknown URLs stay as TODO).

## Reading order

Read the documents in this order:

| # | Document | Purpose |
|---|---|---|
| 0 | [README.md](README.md) | This file — purpose, scope boundary, reading order. |
| 1 | [01_SCOPE.md](01_SCOPE.md) | Exact agency list, total agency-count estimate, what is in/out of v2, which v1 policies stay. |
| 2 | [02_SOURCE_REGISTRY_PLAN.md](02_SOURCE_REGISTRY_PLAN.md) | Per-agency source registry design, required fields, source verification procedure. |
| 3 | [03_BACKFILL_AND_PIPELINE_PLAN.md](03_BACKFILL_AND_PIPELINE_PLAN.md) | Rolling/backfill windows, batch order, extraction strategy, dry-run/staging gates. |
| 4 | [04_DATA_QUALITY_PLAN.md](04_DATA_QUALITY_PLAN.md) | Parse success, masking verification, placeId match rate, entity-resolution dedupe, grade distribution checks, regional sampling. |
| 5 | [05_DB_ROLLOUT_PLAN.md](05_DB_ROLLOUT_PLAN.md) | Pre-injection checklist, promotion criteria, batched rollout, rollback/recompute, API/front-end compatibility. |
| 6 | [06_LEGAL_AND_RISK_PLAN.md](06_LEGAL_AND_RISK_PLAN.md) | Legal/privacy re-confirmation, masking by rank, attribution, complaint handling, per-jurisdiction format risk. |
| 7 | [07_ACCEPTANCE_CRITERIA.md](07_ACCEPTANCE_CRITERIA.md) | Completion criteria for each gate: docs, registry, dry-run, DB injection, deployment. |
| 8 | [08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md](08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md) | **Literal coding-agent harness** for the agency-taxonomy migration + 86 new-agency stubs. Implements [ADR-011](../../adr/ADR-011-agency-taxonomy-model.md). |

> Note: documents 0–7 are planning-only. Document 8 is the one **buildable** spec in this folder — a precise, file-by-file harness meant to be executed by a coding agent (it migrates the `kind` taxonomy and adds the 86 agencies as `adapter_required` stubs with **no** real URLs). It performs no crawl, DB write, or deploy.

## Authority and precedence

- Personal-data exposure policy: **[docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) is the final authority.** Nothing in this folder overrides it.
- Irreversible decisions: governed by the ADRs in [docs/adr/](../../adr/). v2 reuses v1 decisions unless a new ADR supersedes them. v2 introduces exactly **one** new ADR — [ADR-011](../../adr/ADR-011-agency-taxonomy-model.md) (agency taxonomy: `kind` → `gov_tier` + `branch` + `jurisdiction_type`) — which the agency-model migration in [08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md](08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md) implements. Any further decision change would need its own new ADR.
- Attribution: the footer / OpenAPI / `llms.txt` line **"공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외"** must be preserved (and the "외 N개 기관" count updated to reflect the expanded coverage).

## Fact vs. assumption convention

Throughout these documents:

- **[FACT]** — stated in an existing v1 document or in the current codebase, and cited.
- **[ASSUMPTION]** — a reasonable planning assumption that has not been verified against a primary source; must be confirmed before it drives an operational step.
- **[TODO]** — something that must be looked up or decided (e.g., a real board URL) before the corresponding step can run. We do not fabricate values to remove a TODO.
