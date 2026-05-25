# plan2.md — Legal Visibility And Masking Module

## Execution Snapshot

- **Status**: Observed as implemented in the current worktree; final verification/checkpoint still required.
- **Resume point**: Confirm legal visibility validation and public SQL filters, then mark complete in `STATUS.md`.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Create a deep Legal Visibility Module that owns masking validation and public visibility. This is the highest-risk architecture item because `LEGAL_PRIVACY.md` requires DB-stage masking and schema validation, but the current Implementation mostly trusts LLM output.

This plan must be completed before consolidating public read routes.

## Scope Gate

This plan enforces the current Seoul legal policy only. Before any Gyeonggi/Incheon row is normalized, validated, resolved, or loaded, complete `plan2b.md` and update `LEGAL_PRIVACY.md` / `PIPELINE.md` with the capital-area elected-rank allowlist. Until then, any non-Seoul `Agency` passed to the legal validator is a STOP condition, not a best-effort fallback.

## Read First

- `AGENTS.md`
- `docs/LEGAL_PRIVACY.md`
- `docs/RISK_MITIGATION.md`
- `docs/PIPELINE.md` masking section
- `docs/DATA_MODEL.md` SQL function and public view sections
- `services/pipeline/src/public_officer_pipeline/normalizer/llm.py`
- `services/pipeline/src/public_officer_pipeline/normalizer/rules.py`
- `services/pipeline/src/public_officer_pipeline/cli.py`
- `services/pipeline/src/public_officer_pipeline/loader/postgres.py`
- `supabase/migrations/20260523235106_initial.sql`

## Files To Touch

Primary:

- `services/pipeline/src/public_officer_pipeline/legal/__init__.py`
- `services/pipeline/src/public_officer_pipeline/legal/visibility.py`
- `services/pipeline/src/public_officer_pipeline/normalizer/llm.py`
- `services/pipeline/src/public_officer_pipeline/normalizer/rules.py`
- `services/pipeline/src/public_officer_pipeline/loader/postgres.py`
- `services/pipeline/tests/test_masking.py`
- `supabase/migrations/20260523235106_initial.sql` or a new forward migration
- `docs/DATA_MODEL.md`

Use a new forward migration instead of editing the initial migration if any live DB has already applied the initial migration.

## Target Module Interface

Create `public_officer_pipeline.legal.visibility` with:

```python
ALLOWED_ELECTED_RANKS: tuple[str, ...]
APPOINTED_RANKS: tuple[str, ...]

class LegalVisibilityError(ValueError): ...

def sanitize_raw_excerpt(value: str | None) -> str:
    ...

def validate_normalized_visit(visit: NormalizedVisit) -> NormalizedVisit:
    ...

def validate_normalized_visits(visits: list[NormalizedVisit]) -> list[NormalizedVisit]:
    ...
```

Rules for Seoul in this plan:

- `representative` is allowed only when `rank_label` is one of `시장`, `구청장`, `시의원`, `구의원`.
- If `rank_label` is appointed or staff-level, `representative` must be `None`.
- `raw_excerpt` must not preserve personal names. Replace Korean names immediately followed by official rank labels with `○○`.
- `department_name` must not start with a 2-4 Korean character personal name followed by rank labels such as `국장`, `과장`, `팀장`, `담당관`, `전문위원`.
- `purpose` is not hard-rejected for generic Korean words because false positives are high; only sanitize obvious `이름+직급` patterns if present.

수도권 ranks such as `도지사`, `군수`, `도의원`, `광역시의원`, `군의원` are out of enforcement scope until `LEGAL_PRIVACY.md` is explicitly updated. Add tests marked as expected future policy only if the test framework supports that without failing CI.

Do not implement 수도권 rank behavior inside this plan. `plan2b.md` owns that policy expansion.

## SQL Visibility Rules

Ensure public derivations ignore hidden/deleted places:

- `places_public`: already filters `hidden_at IS NULL AND deleted_at IS NULL`; keep it.
- `place_visits_public`: must join only visible places; keep or add filter.
- `place_grade_v1`: must filter `p.hidden_at IS NULL AND p.deleted_at IS NULL`.
- `agency_stats_v1`: must count only visits whose place is visible.

Do not change `request_takedown` immediate-hide behavior.

Review grants:

- Public routes should call `public.report_closure` and `public.request_takedown` through Vercel.
- Do not grant direct `anon` execute on `app_private.*` functions unless an ADR explicitly requires it.
- In the migration, remove direct public access to private implementation functions:
  ```sql
  REVOKE USAGE ON SCHEMA app_private FROM anon, authenticated;
  REVOKE EXECUTE ON FUNCTION app_private.report_closure_impl(uuid, text, text) FROM anon, authenticated;
  REVOKE EXECUTE ON FUNCTION app_private.request_takedown_impl(uuid, text, text) FROM anon, authenticated;
  ```
  Keep `GRANT EXECUTE` only on the public wrapper functions used by Vercel write routes.

## Implementation Steps

1. Add `legal/visibility.py` and `legal/__init__.py`.
2. Move rank constants out of `normalizer/rules.py` or re-export them from `legal.visibility`; avoid duplicate legal constants.
3. Call `sanitize_raw_excerpt` when building `NormalizedVisit` in both LLM and deterministic flows.
4. Call `validate_normalized_visits` before `PostgresLoader.load` receives visits. If plan12 has not happened yet, call it in `cli.py` immediately after normalization and before resolver/loader work.
5. Add a defensive call inside `PostgresLoader.load` as a second line of defense.
6. Patch SQL view definitions according to "SQL Visibility Rules".
7. Update `DATA_MODEL.md` to document that grade and agency stats exclude hidden/deleted places.

## Tests

Add tests to `test_masking.py`:

- elected representative survives when rank is elected.
- appointed official representative raises `LegalVisibilityError` or is normalized to `None` before validation.
- `raw_excerpt` sanitizes `홍길동 국장`, `김철수 과장`, and `박영희 구청장` to `○○ 국장`, etc.
- `department_name="홍길동 국장"` fails validation.
- existing deterministic normalizer tests remain green.

Run:

```bash
npm run test:pipeline
npm run build
rg -n "app_private\\.report_closure_impl|app_private\\.request_takedown_impl|place_grade_v1|agency_stats_v1" supabase/migrations docs/DATA_MODEL.md
```

## Acceptance Criteria

- A legally invalid `NormalizedVisit` cannot reach DB load.
- `raw_excerpt` does not store obvious personal names.
- Hidden/deleted places cannot affect public views, grade rankings, or agency stats.
- Legal rank policy has one Module Interface.

## STOP Conditions

- If existing fixtures contain raw personal names that cannot be sanitized without changing expected legal policy, stop and report the exact fixture.
- If a live DB has applied the initial migration, do not edit it in place. Create a new migration.
- If 수도권 elected-rank policy is required for current data, stop and update `LEGAL_PRIVACY.md` first in a separate reviewed change.
- If any non-Seoul agency can reach `validate_normalized_visit` before `plan2b.md` is complete, stop and report the missing policy gate.
