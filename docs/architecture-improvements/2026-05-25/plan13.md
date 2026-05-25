# plan13.md — Frontend Place Explorer Module Overview

## Execution Snapshot

- **Status**: Coordinator only; do not execute directly.
- **Resume point**: After plan12, choose `plan13a.md`, then `plan13b.md`, then `plan13c.md`.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Direct Execution Policy

Do not execute this file as an implementation plan. It is the coordination overview for the frontend split. Execute these smaller plans instead:

1. `plan13a.md` — pure helpers, query state, formatters, and public data Module.
2. `plan13b.md` — Kakao loader, marker image, `MapCanvas`, and `FallbackMap`.
3. `plan13c.md` — panels, static pages, forms, CSS split, and browser QA.

If an implementation harness is pointed at `plan13.md` directly, STOP and switch to `plan13a.md`.

## Objective

Coordinate the split of `App.tsx` into a deep Place Explorer Module after public contracts stabilize. Current `App.tsx` owns static route dispatch, query state, fetches, Kakao map, fallback map, marker SVG, list/detail panels, report modals, static legal pages, formatting, and browser fingerprinting.

## Prerequisites

Complete these first:

- plan3 public route policy
- plan4 route contract registry
- plan5 agency/region registry

Do not start this refactor before API and region Interfaces are stable.

## Read First

- `docs/UI_UX.md`
- `docs/retouch/001_260525/*`
- `apps/web/src/App.tsx`
- `apps/web/src/styles.css`
- `apps/web/package.json`

## Files To Touch

Primary new structure:

```text
apps/web/src/app/App.tsx
apps/web/src/app/staticPages.tsx
apps/web/src/features/place-explorer/index.ts
apps/web/src/features/place-explorer/PlaceExplorer.tsx
apps/web/src/features/place-explorer/types.ts
apps/web/src/features/place-explorer/queryState.ts
apps/web/src/features/place-explorer/publicData.ts
apps/web/src/features/place-explorer/format.ts
apps/web/src/features/place-explorer/map/MapCanvas.tsx
apps/web/src/features/place-explorer/map/kakaoLoader.ts
apps/web/src/features/place-explorer/map/markerImage.ts
apps/web/src/features/place-explorer/map/FallbackMap.tsx
apps/web/src/features/place-explorer/panels/PlaceList.tsx
apps/web/src/features/place-explorer/panels/PlaceDetails.tsx
apps/web/src/features/place-explorer/panels/BottomSheet.tsx
apps/web/src/features/place-explorer/forms/reportFlows.ts
apps/web/src/features/place-explorer/styles.css
```

Existing:

- `apps/web/src/App.tsx`
- `apps/web/src/main.tsx`
- `apps/web/src/styles.css`

The implementer may keep fewer files if the Interface remains deep, but must separate query state, data reading, map Adapter, panels, and static pages.

## Target Interfaces

### Page Interface

`apps/web/src/App.tsx` should only choose between static pages and the map experience.

```tsx
export function App() {
  return <AppRoutes />;
}
```

### Place Explorer Interface

```tsx
export function PlaceExplorer(): JSX.Element;
```

Callers should not know fetch ordering, Kakao script loading, marker construction, or modal state.

### Query State Interface

```ts
export type PlaceQueryState = {
  q: string;
  region: string[];
  grade: Grade[];
  sort: SortMode;
  placeId: string | null;
};

export function parseQueryState(search?: string): PlaceQueryState;
export function serializeQueryState(state: PlaceQueryState): string;
export function normalizeQueryState(state: PlaceQueryState): PlaceQueryState;
```

### Public Data Interface

```ts
export function loadPlaces(query: Pick<PlaceQueryState, 'grade'>): Promise<Place[]>;
export function searchPlaces(query: PlaceQueryState, signal?: AbortSignal): Promise<Place[]>;
export function loadRegions(): Promise<Region[]>;
export function loadPlaceById(id: string): Promise<Place>;
export function loadVisits(placeId: string): Promise<Visit[]>;
```

## Implementation Steps

1. Move types and pure helpers first:
   - `types.ts`
   - `queryState.ts`
   - `format.ts`
2. Add Vitest tests for pure helpers before moving JSX.
3. Move public fetch functions to `publicData.ts`.
4. Move Kakao loader and marker image code into map files.
5. Move `FallbackMap` unchanged.
6. Move panels unchanged.
7. Move report/takedown submit helpers into `reportFlows.ts` only if it reduces parent state; otherwise leave inside `PlaceExplorer`.
8. Move static page content out of the map feature.
9. Create feature-level CSS by moving only place-explorer styles; keep global app reset/base styles in `styles.css`.
10. Preserve current UX:
    - no map data loading overlay
    - marker labels legible in list and map
    - sort control does not overflow
    - mobile bottom sheet behavior unchanged
    - source notice visible

## Tests

Add Vitest tests:

- query parsing defaults to `★★★,★★,✦`.
- `serializeQueryState(parseQueryState(x))` preserves supported params.
- `sortPlaces` behavior for `score`, `recent`, and `visits`.
- `shortRegionLabel` or equivalent handles `서울`, `경기`, `인천`.
- `gradeLabel`, `markerLabel`, `gradeClass` mappings.

Run:

```bash
npm --workspace apps/web run test
npm run build
```

Manual QA after local dev server:

- Desktop: search, region filter, grade filter, sort, list open/close, marker click, detail drawer.
- Mobile: search, bottom nav, filter panel, detail sheet, close/back behavior.
- Forms: closure report and takedown request still submit to the same endpoints.

## Acceptance Criteria

- `App.tsx` is no longer the owner of map, data, panels, forms, static pages, and formatting Implementation.
- Query state and formatting are tested without rendering the full app.
- The Place Explorer Module has high Depth: one caller Interface, many internal behaviors.
- No visual regression from the latest deployed UI fixes.

## STOP Conditions

- If moving CSS causes layout regressions that cannot be resolved quickly, keep CSS in `styles.css` and only split TypeScript/TSX first.
- If component tests require new frontend testing dependencies, do not add them in this plan; rely on pure Vitest tests and manual QA.
