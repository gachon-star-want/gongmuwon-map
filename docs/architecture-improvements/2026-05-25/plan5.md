# plan5.md — Agency And Region Registry Module

## Execution Snapshot

- **Status**: Observed as implemented in the current worktree; final verification/checkpoint still required.
- **Resume point**: Confirm agency/region registry behavior and API surface, then mark complete in `STATUS.md`.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Create a deep Agency/Region Registry Module for 수도권. Current agency identity lives in Python, public region metadata lives in `api/v1/regions.ts`, UI label logic strips only `서울`, and docs contain stale taxonomy wording. This plan makes the public region Interface explicit before any 수도권 data is surfaced.

## Read First

- `docs/adr/ADR-011-agency-taxonomy-model.md`
- `docs/v2/001_capital_area_expansion/01_SCOPE.md`
- `docs/v2/001_capital_area_expansion/02_SOURCE_REGISTRY_PLAN.md`
- `docs/v2/001_capital_area_expansion/07_ACCEPTANCE_CRITERIA.md`
- `services/pipeline/src/public_officer_pipeline/agencies.py`
- `api/v1/regions.ts`
- `apps/web/src/App.tsx` region and label helpers

## Files To Touch

Primary:

- `api/_lib/region-registry.ts` (new)
- `api/v1/regions.ts`
- `apps/web/src/App.tsx`
- `services/pipeline/tests/test_agencies.py`
- `docs/v2/001_capital_area_expansion/02_SOURCE_REGISTRY_PLAN.md`
- `docs/v2/001_capital_area_expansion/07_ACCEPTANCE_CRITERIA.md`

Do not change agency UUID generation in this plan.

## Target Interface

Create `api/_lib/region-registry.ts`:

```ts
export type PublicRegionMeta = {
  region: string; // road_address_part, e.g. "서울 강남구", "경기 수원시", "인천 강화군"
  label: string;  // display label, e.g. "강남구", "수원시", "강화군"
  parent_region: '서울' | '경기' | '인천';
  jurisdiction_type: 'special_city' | 'metro_city' | 'province' | 'autonomous_gu' | 'si' | 'gun';
  center: { latitude: number; longitude: number };
  bbox: {
    min_latitude: number;
    min_longitude: number;
    max_latitude: number;
    max_longitude: number;
  };
  estimated: boolean;
  metadata_source: 'exact' | 'parent_region_fallback';
};

export function regionLabel(region: string): string;
export function regionMeta(region: string): PublicRegionMeta | null;
export function fallbackRegionMeta(region: string): PublicRegionMeta;
export const SEOUL_REGION_METADATA: Record<string, PublicRegionMeta>;
export const CAPITAL_AREA_REGION_METADATA: Record<string, PublicRegionMeta>;
```

For this plan, exact Gyeonggi/Incheon centers and bboxes may be coarse if not already verified, but the data shape must explicitly mark them as estimated. Do not invent source URLs or pretend estimated coordinates are exact.

## Implementation Decisions

- Python agency registry remains source of truth for agency IDs and crawl status.
- TypeScript region registry becomes source of truth for public map/filter metadata.
- `/api/v1/regions` must include rows from DB even when metadata is missing; unknown metadata uses `fallbackRegionMeta`.
- `include_empty=true` returns known registry regions, not just Seoul.
- UI label helper must no longer strip only `서울`; it should use region metadata from API where possible and a generic fallback for `서울|경기|인천`.

## Implementation Steps

1. Move existing `SEOUL_REGIONS` from `api/v1/regions.ts` into `api/_lib/region-registry.ts`.
2. Add Gyeonggi/Incheon registry entries only at the jurisdiction level from ADR-011:
   - Gyeonggi: 31 `시/군`
   - Incheon: 10 `군/구`
3. Use conservative bbox/center data:
   - If exact values are not in repo, use parent-region fallback for `include_empty` and set `estimated: true`, `metadata_source: "parent_region_fallback"`.
   - For Seoul entries already present in code, set `estimated: false`, `metadata_source: "exact"`.
   - Do not block `/api/v1/regions` for missing exact bbox.
4. Update `/api/v1/regions`:
   - Use `CAPITAL_AREA_REGION_METADATA`.
   - For `include_empty=false`, return all DB regions, not only metadata-known Seoul rows.
   - For unknown DB regions, use fallback center/bbox by parent region.
5. Update frontend `shortRegionLabel`:
   - `서울 강남구` -> `강남구`
   - `경기 수원시` -> `수원시`
   - `인천 강화군` -> `강화군`
   - unknown -> original string
6. Update docs to use ADR-011 enum names.

## Tests

Add/extend tests where practical:

- API helper test for `regionLabel`.
- Static test that `CAPITAL_AREA_REGION_METADATA` contains all current `road_address_part` forms expected by v2 scope.
- Pipeline agency tests already verify `52 / 64 / 22 / 138`; keep them green.

Run:

```bash
npm run build
npm run test:pipeline
rg -n "city\\|county\\|gu\\|kind" docs/v2/001_capital_area_expansion
```

Manual API smoke after build/deploy-capable environment:

```text
GET /api/v1/regions
GET /api/v1/regions?include_empty=1
```

## Acceptance Criteria

- `/api/v1/regions` no longer filters out non-Seoul DB rows.
- Frontend labels support `서울`, `경기`, and `인천`.
- Region metadata has one TypeScript Module Interface.
- Agency identity and public region metadata are intentionally connected by tests/docs, not by scattered literals.

## STOP Conditions

- If exact bbox data is required for launch and unavailable locally, stop and mark the affected entries as TODO instead of fabricating exact coordinates.
- If changing `/api/v1/regions?include_empty=1` would break current UI assumptions, stop and add a compatibility note before changing behavior.
