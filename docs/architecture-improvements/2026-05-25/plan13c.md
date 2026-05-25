# plan13c.md — Frontend Panels, Static Pages, Forms, And CSS Split

## Execution Snapshot

- **Status**: Pending.
- **Resume point**: Start only after plan13b is complete.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Finish the frontend Place Explorer split after helpers and map code are stable. Move list/detail panels, bottom sheet, report flows, static pages, and feature CSS out of `App.tsx` while preserving the current UX.

## Prerequisites

- `plan13a.md` is complete.
- `plan13b.md` is complete.

## Read First

- `apps/web/src/App.tsx`
- `apps/web/src/styles.css`
- `apps/web/src/features/place-explorer/types.ts`
- `apps/web/src/features/place-explorer/queryState.ts`
- `apps/web/src/features/place-explorer/publicData.ts`
- `docs/UI_UX.md`
- `docs/retouch/001_260525/04_interaction_spec.md`
- `docs/retouch/001_260525/05_visual_design_spec.md`
- `docs/retouch/001_260525/08_test_and_acceptance.md`

## Files To Touch

Primary:

```text
apps/web/src/app/App.tsx
apps/web/src/app/staticPages.tsx
apps/web/src/features/place-explorer/index.ts
apps/web/src/features/place-explorer/PlaceExplorer.tsx
apps/web/src/features/place-explorer/panels/PlaceList.tsx
apps/web/src/features/place-explorer/panels/PlaceDetails.tsx
apps/web/src/features/place-explorer/panels/BottomSheet.tsx
apps/web/src/features/place-explorer/panels/MobileFilterPanel.tsx
apps/web/src/features/place-explorer/panels/MobileInfoPanel.tsx
apps/web/src/features/place-explorer/forms/reportFlows.ts
apps/web/src/features/place-explorer/styles.css
apps/web/src/App.tsx
apps/web/src/main.tsx
apps/web/src/styles.css
```

The implementer may keep fewer panel files only if `PlaceExplorer.tsx` remains the single caller-facing Interface and `App.tsx` only dispatches routes.

## Target Interfaces

`apps/web/src/App.tsx`:

```tsx
export { App } from "./app/App";
```

`apps/web/src/app/App.tsx`:

```tsx
export function App(): JSX.Element;
```

`PlaceExplorer.tsx`:

```tsx
export function PlaceExplorer(): JSX.Element;
```

`reportFlows.ts`:

```ts
export function browserFingerprint(): string;
export function submitClosureReport(input: { placeId: string; note: string | null }): Promise<unknown>;
export function submitTakedownRequest(input: { placeId: string; reason: string; email: string | null }): Promise<unknown>;
```

## CSS Split Rules

- Move only place-explorer styles into `features/place-explorer/styles.css`.
- Keep global reset/base/app-shell styles in `apps/web/src/styles.css`.
- If moving CSS creates layout regressions, stop CSS movement and leave a TODO; do not weaken layout constraints.

## UX Preservation Checklist

- no map data loading overlay
- marker labels legible in list and map
- sort control does not overflow
- mobile bottom sheet behavior unchanged
- source notice visible on map and static pages
- report/takedown modals submit to `/api/closure-report` and `/api/takedown-request`
- no comments, ratings, reviews, likes, or community UI added

## Tests

Run:

```bash
npm --workspace apps/web run test
npm run build
```

Manual QA:

```bash
npm run dev -- --port 5173
```

Open `http://localhost:5173` and test:

- Desktop: search, region filter, grade filter, sort, list open/close, marker click, detail drawer.
- Mobile viewport: search, bottom nav, filter panel, detail sheet, close/back behavior.
- Static routes: `/about`, `/privacy`, `/terms`, `/disclaimer`, `/legal`, `/api`.
- Forms: closure report and takedown request still call the same endpoints.

## Acceptance Criteria

- `App.tsx` is a route shell, not the owner of map, fetches, panels, forms, static pages, and formatting.
- Place Explorer has one caller Interface.
- Tests and build pass.
- Manual QA finds no material visual regression.

## STOP Conditions

- If component extraction causes state behavior regressions, stop after moving static pages and panels; do not also move CSS.
- If CSS movement causes mobile or desktop layout overlap, revert only the CSS move and leave TypeScript/TSX split intact.
- If form extraction changes legal/takedown behavior, stop and keep submit logic in `PlaceExplorer.tsx` until a smaller form plan is written.
