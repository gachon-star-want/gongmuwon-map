# plan1.md — Public Agency Schema Hotfix And ADR-011 Consistency

## Execution Snapshot

- **Status**: Observed as implemented in the current worktree; final verification/checkpoint still required.
- **Resume point**: Confirm the `kind` removal path and ADR-011 public agency fields, then mark complete in `STATUS.md`.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Repair the current `kind` drift introduced by ADR-011. The database schema, `agencies_public` view, pipeline model, loader, and seed now expose `gov_tier`, `branch`, and `jurisdiction_type`; `/api/v1/agencies` still queries `kind`, and several v2 docs still describe `kind` as unresolved.

This plan is a hotfix plus documentation consistency pass. Do this before deeper architecture work.

## Read First

- `AGENTS.md`
- `docs/adr/ADR-011-agency-taxonomy-model.md`
- `docs/DATA_MODEL.md`
- `docs/v2/001_capital_area_expansion/08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md`
- `api/v1/agencies.ts`
- `supabase/migrations/20260523235106_initial.sql`

## Files To Touch

Primary:

- `api/v1/agencies.ts`
- `docs/v2/001_capital_area_expansion/02_SOURCE_REGISTRY_PLAN.md`
- `docs/v2/001_capital_area_expansion/04_DATA_QUALITY_PLAN.md`
- `docs/v2/001_capital_area_expansion/05_DB_ROLLOUT_PLAN.md`
- `docs/v2/001_capital_area_expansion/07_ACCEPTANCE_CRITERIA.md`
- `docs/v2/001_capital_area_expansion/01_SCOPE.md`
- `docs/v2/001_capital_area_expansion/08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md`

Only touch other files if a verification command proves another stale `kind` reference in the same contract area.

## Target Interface

The public agency JSON rows must expose:

```ts
{
  id: string;
  name: string;
  short_name: string;
  gov_tier: 'regional' | 'basic';
  branch: 'admin' | 'council';
  jurisdiction_type: 'special_city' | 'metro_city' | 'province' | 'autonomous_gu' | 'si' | 'gun';
  parent_region: string;
  sub_region: string | null;
  homepage: string | null;
  visit_count: number | string;
  place_count: number | string;
  last_visit_at: string | null;
}
```

Do not add a compatibility `kind` field. ADR-011 explicitly says public consumers read the three new fields.

## Implementation Steps

1. Check current worktree:
   ```bash
   git status --short
   ```
2. Patch `api/v1/agencies.ts`:
   - Replace `kind` in the `SELECT` list with `gov_tier, branch, jurisdiction_type`.
   - Replace `ORDER BY kind, sub_region NULLS FIRST, short_name` with:
     ```sql
     ORDER BY gov_tier, branch, parent_region, sub_region NULLS FIRST, short_name
     ```
   - Keep `methodGuard`, `sendJson`, cache behavior, and route shape unchanged.
3. Patch docs:
   - In v2 rollout/checklist docs, replace any wording that says `kind` is unresolved with wording that ADR-011 resolved it using `gov_tier + branch + jurisdiction_type`.
   - In source registry docs, replace `city/county/gu` taxonomy labels with ADR-011 values: `si`, `gun`, `autonomous_gu`.
   - In `01_SCOPE.md`, keep historical examples only where they explicitly say the old `kind` values were superseded by ADR-011.
   - In `08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md`, keep implementation-history references only if they name the old field as removed/superseded.
   - Keep historical mentions in ADR-011 itself. Do not rewrite ADR context.
4. Run targeted search:
   ```bash
   rg -n "\bkind\b" api docs/v2 docs/DATA_MODEL.md docs/adr/ADR-011-agency-taxonomy-model.md
   ```
   Acceptable remaining matches:
   - ADR-011 historical explanation.
   - This plan folder.
   - Any doc explicitly saying old `kind` was superseded.
   - `01_SCOPE.md` and `08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md` only where the match is part of an ADR-011 migration/history explanation, not a current blocker or current schema instruction.
   Unacceptable remaining matches:
   - API SQL selecting `kind`.
   - v2 gate saying `kind` is unresolved.
   - registry values `city/county/gu` where ADR-011 enum values are required.

## Tests And Verification

Run:

```bash
npm run build
npm run test:pipeline
rg -n "\bkind\b" api docs/v2 docs/DATA_MODEL.md docs/adr/ADR-011-agency-taxonomy-model.md
```

If there is no API test harness, do not invent one in this hotfix. The build plus grep is enough for this plan.

## Acceptance Criteria

- `/api/v1/agencies` cannot reference `kind`.
- Public agency rows use `gov_tier`, `branch`, and `jurisdiction_type`.
- v2 docs no longer describe the agency taxonomy schema question as unresolved.
- No Seoul agency ID or source pattern changes.

## STOP Conditions

- If `agencies_public` in the active migration/view still exposes `kind`, stop and report the schema mismatch.
- If any deployed external contract explicitly depends on `kind`, stop and ask for an ADR or compatibility decision before adding aliases.
