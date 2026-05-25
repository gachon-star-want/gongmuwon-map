# Architecture Improvement Harness — 2026-05-25

This folder is the recurring home for `$improve-codebase-architecture` outputs.

These documents are written as implementation harnesses for `gpt-5.3-codex-spark`: each plan must be executable without inventing architecture decisions. If a plan conflicts with current repo reality, the implementer must stop and report the exact conflict before patching.

## Architecture Vocabulary

Use these terms consistently in implementation notes and follow-up reviews.

- **Module**: anything with an Interface and Implementation.
- **Interface**: everything a caller must know to use a Module correctly: types, invariants, config, ordering, error modes, and performance assumptions.
- **Implementation**: code inside a Module.
- **Depth**: Leverage at the Interface; a deep Module hides lots of behavior behind a small Interface.
- **Seam**: where an Interface lives.
- **Adapter**: concrete thing satisfying an Interface at a Seam.
- **Leverage**: what callers get from Depth.
- **Locality**: what maintainers get from Depth.
- **deletion test**: if deleting a Module spreads complexity across callers, the Module earns its keep.

## Execution Rules For Every Plan

1. Read `AGENTS.md` and the plan's "Read First" section before editing.
2. Check `git status --short` before editing. Do not revert unrelated user changes.
3. Make only the changes named in the current plan. Do not opportunistically start later plans.
4. If a plan says "STOP", stop immediately and report. Do not invent a workaround.
5. Prefer small commits or checkpoints per plan.
6. After implementation, run the exact verification commands from the plan.
7. If a command cannot run because dependencies or credentials are missing, report the command and the reason.

## Resume Protocol

Use [STATUS.md](STATUS.md) as the first file to read before any plan. It is the only place that should carry cross-plan progress.

1. Open `STATUS.md`, then open exactly one current plan.
2. Read only that plan's `Read First` files and the files listed under `Files To Touch`.
3. Do not paste full prior transcripts, full diffs, or full command logs into a new model context. Summarize them in 30 lines or less and point to files when possible.
4. If a task needs more than one context window, stop at a substep boundary and update `STATUS.md` before continuing.
5. If compaction or context overflow happens, restart from `STATUS.md` and the current plan file only.

## Status Ledger

Current observed progress and resume points live in [STATUS.md](STATUS.md). The status ledger is intentionally short and should be updated more often than the individual plan documents.

## Recommended Sequence

| Order | Plan | Why It Comes Here |
|---:|---|---|
| 1 | [plan1.md](plan1.md) — Public agency schema hotfix and ADR-011 consistency | Current public route can break because it still queries `kind`. |
| 2 | [plan2.md](plan2.md) — Legal visibility and masking Module | Legal safety must precede public read consolidation. |
| 3 | [plan2b.md](plan2b.md) — Capital-area legal rank policy | Required before any non-Seoul normalization/load can be legal-safe. |
| 4 | [plan3.md](plan3.md) — Public route policy and read Module | Locks readonly/write behavior after legal visibility is correct. |
| 5 | [plan3b.md](plan3b.md) — Public route policy tests | Pins method/CORS/cache/DB-role behavior before contract consolidation. |
| 6 | [plan4.md](plan4.md) — Public route contract registry Module | Prevents docs/OpenAPI/rewrites from drifting again. |
| 7 | [plan5.md](plan5.md) — Agency and region registry Module | Needed before 수도권 UI/API surfacing. |
| 8 | [plan6.md](plan6.md) — Place resolution policy Module | Needed for 수도권 `road_address_part` and ADR-003 correctness. |
| 9 | [plan7.md](plan7.md) — Source pattern and crawler Adapter Module | Makes crawler expansion safer. |
| 10 | [plan8.md](plan8.md) — Source artifact Module | Centralizes fetch/hash/provenance before storage/orchestration refactor. |
| 11 | [plan8b.md](plan8b.md) — R2 source storage Adapter | Makes raw-source preservation real before load batches depend on it. |
| 12 | [plan9.md](plan9.md) — LLM routing Module | Adds the provider-routing Seam. |
| 13 | [plan9b.md](plan9b.md) — LLM usage and budget guardrail | Completes ADR-009 operational requirements after routing exists. |
| 14 | [plan10.md](plan10.md) — Expense row construction Module | Centralizes parsing shared by extractors. |
| 15 | [plan11.md](plan11.md) — PDF layout grammar Module | Splits the largest extractor after row construction exists. |
| 16 | [plan12.md](plan12.md) — Pipeline run, load batch, and quality gate Modules | Rewires orchestration after lower-level Interfaces are stable. |
| 17 | [plan13a.md](plan13a.md) — Frontend pure helpers and data Module | Starts frontend split with low-risk tested pure code. |
| 18 | [plan13b.md](plan13b.md) — Frontend map Adapter Module | Extracts Kakao/fallback map behavior after data contracts are stable. |
| 19 | [plan13c.md](plan13c.md) — Frontend panels, static pages, and CSS split | Finishes the UI refactor after helpers and map seams are stable. |

## Global Verification Matrix

Run these after each plan unless the plan narrows the required set. If output is long, record only pass/fail plus the first actionable error in `STATUS.md`.

```bash
git status --short
npm run build
npm run test:pipeline
```

Optional, when relevant:

```bash
npm --workspace apps/web run test
rg -n "\bkind\b" api docs/v2 docs/DATA_MODEL.md
rg -n "DATABASE_URL_READONLY|request_takedown|report_closure" api supabase docs
```

Note: at the start of this harness, `npm --workspace apps/web run test` exits with code 1 because no frontend test files exist. The first plan that requires that command to pass is `plan13a.md`, which must add the initial Vitest files.

## Current Known High-Risk Findings

This list is historical until re-verified against the current worktree. Prefer `STATUS.md` for the latest observed state.


- `/api/v1/agencies` still selects `kind` although ADR-011 removed it from `agencies_public`.
- `api/_lib/db.ts` falls back from `DATABASE_URL_READONLY` to `DATABASE_URL`.
- `place_grade_v1` and `agency_stats_v1` can count hidden/deleted places unless filtered.
- Docs, OpenAPI, rewrites, and implementation advertise different route sets.
- `road_address_part` extraction is Seoul-only.
- `KakaoResolver` does not fully implement ADR-003 matching/fallback/cache policy.
- LLM routing in code does not yet implement ADR-009's unified Interface.
