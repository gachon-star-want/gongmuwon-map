# plan13b.md — Frontend Map Adapter Module

## Execution Snapshot

- **Status**: Pending.
- **Resume point**: Start only after plan13a is complete.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Extract the Kakao map integration and fallback map from `App.tsx` behind a map Adapter Module. This plan should preserve the existing marker behavior and viewport behavior.

## Prerequisites

- `plan13a.md` is complete.

## Read First

- `apps/web/src/App.tsx`
- `apps/web/src/features/place-explorer/types.ts`
- `apps/web/src/features/place-explorer/format.ts`
- `apps/web/src/styles.css`

## Files To Touch

Primary:

- `apps/web/src/features/place-explorer/map/MapCanvas.tsx` (new)
- `apps/web/src/features/place-explorer/map/FallbackMap.tsx` (new)
- `apps/web/src/features/place-explorer/map/kakaoLoader.ts` (new)
- `apps/web/src/features/place-explorer/map/markerImage.ts` (new)
- `apps/web/src/features/place-explorer/map/geo.ts` (new if useful)
- `apps/web/src/features/place-explorer/map/geo.test.ts` (new)
- `apps/web/src/App.tsx`

Do not split panels, static pages, forms, or CSS in this plan.

## Target Interfaces

`MapCanvas.tsx`:

```tsx
export function MapCanvas(props: {
  places: Place[];
  selectedPlace: Place | null;
  onSelect: (place: Place) => void;
  onBlankClick: () => void;
}): JSX.Element;
```

`kakaoLoader.ts`:

```ts
export function loadKakao(appKey: string): Promise<void>;
```

`markerImage.ts`:

```ts
export function createMarkerImage(kakao: any, place: Place, selected: boolean): any;
```

`geo.ts`:

```ts
export const SEOUL_CENTER: { latitude: number; longitude: number };
export function positionStyle(latitude: number, longitude: number): { left: string; top: string };
export function average(values: number[]): number;
```

## Decisions

- Keep `VITE_KAKAO_JS_KEY` lookup inside the map Module.
- Keep marker SVG output byte-equivalent unless TypeScript extraction forces trivial formatting changes.
- Preserve current clusterer options and fallback-map clustering threshold.
- Do not add a map testing dependency; test only pure `geo.ts` helpers.

## Tests

Run:

```bash
npm --workspace apps/web run test
npm run build
```

Manual browser check after implementation:

```bash
npm run dev -- --port 5173
```

Open `http://localhost:5173` and verify:

- Kakao map renders when `VITE_KAKAO_JS_KEY` is set.
- Fallback map renders when the key is missing.
- Marker click opens the same detail state.
- Blank map click clears the selected place.

## Acceptance Criteria

- `App.tsx` imports `MapCanvas` instead of owning Kakao loader, marker image, and fallback map code.
- Map behavior and marker labels are unchanged.
- No CSS movement occurs yet.

## STOP Conditions

- If extracted map code needs new browser/map test dependencies, stop and keep this plan to pure extraction plus manual QA.
- If marker rendering changes visibly, revert the marker extraction and report the mismatch.
