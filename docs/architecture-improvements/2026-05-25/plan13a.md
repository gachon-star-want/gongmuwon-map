# plan13a.md — Frontend Pure Helpers And Public Data Module

## Execution Snapshot

- **Status**: Pending.
- **Resume point**: Start only after plan12 is complete.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Start the frontend split by moving pure logic and API fetch functions out of `apps/web/src/App.tsx`. This plan must not move the Kakao map, panels, static pages, or CSS yet.

## Prerequisites

- `plan3.md`, `plan3b.md`, `plan4.md`, and `plan5.md` are complete.

## Read First

- `apps/web/src/App.tsx`
- `apps/web/src/styles.css`
- `apps/web/package.json`
- `docs/UI_UX.md`
- `docs/retouch/001_260525/06_api_contract.md`

## Files To Touch

Primary:

- `apps/web/src/features/place-explorer/types.ts` (new)
- `apps/web/src/features/place-explorer/queryState.ts` (new)
- `apps/web/src/features/place-explorer/format.ts` (new)
- `apps/web/src/features/place-explorer/publicData.ts` (new)
- `apps/web/src/features/place-explorer/queryState.test.ts` (new)
- `apps/web/src/features/place-explorer/format.test.ts` (new)
- `apps/web/src/features/place-explorer/publicData.test.ts` (new only if fetch can be tested with fake `fetch`)
- `apps/web/src/App.tsx`

Do not touch `styles.css` in this plan.

## Target Interfaces

`types.ts` exports `Grade`, `SortMode`, `Place`, `Visit`, `Region`, `SearchResponse`, and `RegionsResponse`.

`queryState.ts`:

```ts
export type PlaceQueryState = {
  q: string;
  region: string[];
  grade: Grade[];
  sort: SortMode;
  placeId: string | null;
};

export const defaultGrades: Grade[];
export function parseQueryState(search?: string): PlaceQueryState;
export function normalizeQueryState(state: PlaceQueryState): PlaceQueryState;
export function serializeQueryState(state: PlaceQueryState): string;
```

`format.ts`:

```ts
export function sortPlaces(places: Place[], sort: SortMode): Place[];
export function formatDate(value: string | null | undefined): string | null;
export function gradeLabel(grade: string): string;
export function markerLabel(grade: string): string;
export function gradeClass(grade: string): string;
export function shortRegionLabel(region: string): string;
```

`publicData.ts`:

```ts
export function loadPlaces(query: Pick<PlaceQueryState, "grade">): Promise<Place[]>;
export function searchPlaces(query: PlaceQueryState, signal?: AbortSignal): Promise<SearchResponse>;
export function loadRegions(): Promise<RegionsResponse>;
export function loadPlaceById(id: string): Promise<Place>;
export function loadVisits(placeId: string): Promise<Visit[]>;
```

## Decisions

- Preserve current default grades: `★★★,★★,✦`.
- `shortRegionLabel` must support:
  - `서울 강남구` -> `강남구`
  - `경기 수원시` -> `수원시`
  - `인천 강화군` -> `강화군`
  - unknown -> original string
- `publicData.ts` owns `API_BASE` and URL construction.
- Existing `App.tsx` may still own React state and JSX after this plan; it should import helpers instead of defining them inline.

## Tests

Add Vitest tests:

- `parseQueryState("")` defaults to `q=""`, `region=[]`, `grade=["★★★","★★","✦"]`, `sort="score"`, `placeId=null`.
- `serializeQueryState(parseQueryState(x))` preserves supported params and drops unsupported params.
- invalid grades fall back to defaults.
- `sortPlaces` behavior for `score`, `recent`, and `visits`.
- `shortRegionLabel` handles Seoul/Gyeonggi/Incheon.
- `gradeLabel`, `markerLabel`, `gradeClass` mappings.

Run:

```bash
npm --workspace apps/web run test
npm run build
```

## Acceptance Criteria

- First frontend test files exist, so `npm --workspace apps/web run test` passes.
- `App.tsx` no longer defines query parsing, sorting, formatting, or fetch URL construction inline.
- Rendered UI behavior remains unchanged.

## STOP Conditions

- If moving helpers changes TypeScript public types used by JSX, stop and keep compatibility re-exports.
- If fetch tests require browser rendering libraries, skip `publicData.test.ts` and test only pure URL construction with a fake `fetch`.
