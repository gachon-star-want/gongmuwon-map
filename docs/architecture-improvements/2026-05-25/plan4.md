# plan4.md — Public Route Contract Registry Module

## Execution Snapshot

- **Status**: Observed as implemented in the current worktree; final verification/checkpoint still required.
- **Resume point**: Confirm public route registry, docs, OpenAPI, and llms.txt alignment, then mark complete in `STATUS.md`.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Create one route contract registry so docs, OpenAPI, llms files, sitemap, Vercel rewrites, and frontend static routes cannot drift independently.

Known drift:

- Docs mention `/agency/{agency_id}` and `/api/v1/agencies/{id}/top-places`, but implementation does not consistently provide them.
- OpenAPI advertises cursor behavior for search, while the route returns `next_cursor: null`.
- SPA rewrites and frontend route rendering are not validated from one Interface.

## Read First

- `docs/PUBLIC_API.md`
- `docs/UI_UX.md`
- `docs/retouch/001_260525/06_api_contract.md`
- `apps/web/public/openapi.json`
- `apps/web/public/llms.txt`
- `apps/web/public/llms-full.txt`
- `vercel.json`
- `api/sitemap.ts`
- `apps/web/src/App.tsx` static route handling

## Files To Touch

Primary:

- `docs/public-route-contracts.json` (new)
- `scripts/verify-public-route-contracts.mjs` (new)
- `package.json`
- `docs/PUBLIC_API.md`
- `apps/web/public/openapi.json`
- `apps/web/public/llms.txt`
- `apps/web/public/llms-full.txt`
- `vercel.json`
- `api/sitemap.ts`

Only touch frontend route code if static paths are missing from the registry.

## Target Registry Shape

Create `docs/public-route-contracts.json`:

```json
{
  "routes": [
    {
      "path": "/api/v1/places",
      "kind": "json",
      "method": "GET",
      "status": "implemented",
      "cache": "public, s-maxage=300, stale-while-revalidate=600",
      "source_notice_required": true,
      "documented_in_openapi": true,
      "documented_in_llms": true
    }
  ]
}
```

Allowed `status` values:

- `implemented`
- `planned`
- `removed_from_public_docs`

No route may be documented as callable in OpenAPI or llms files unless `status="implemented"`.

## Route Decisions For This Plan

- Keep implemented API routes already present.
- For `/api/v1/agencies/{id}/top-places`, choose `planned` and remove it from callable OpenAPI/llms docs unless implemented in the same plan.
- For `/agency/{agency_id}`, choose `planned` and remove user-facing rewrite/docs unless implemented.
- For search cursor:
  - If implementation still returns `next_cursor: null`, document cursor as planned, not active.
  - Do not implement pagination in this plan unless required by existing UI.

## Verification Script Requirements

`scripts/verify-public-route-contracts.mjs` must:

- Load `docs/public-route-contracts.json`.
- Load `apps/web/public/openapi.json`.
- Fail if OpenAPI contains a callable path not marked `implemented`.
- Fail if an implemented JSON route with `source_notice_required=true` is missing from llms docs.
- Fail if a planned route is advertised as implemented.
- Validate JSON schema minimally without adding dependencies.

Add package script:

```json
"check:public-contracts": "node scripts/verify-public-route-contracts.mjs"
```

## Tests

Run:

```bash
npm run check:public-contracts
npm run build
```

Also manually inspect:

```bash
rg -n "top-places|/agency/|cursor|next_cursor" docs apps/web/public api vercel.json
```

## Acceptance Criteria

- There is one registry Interface for public route truth.
- OpenAPI and llms files do not advertise unimplemented routes as callable.
- Search cursor behavior is accurately documented.
- Future route additions have a validation path.

## STOP Conditions

- If a route is externally required but not implemented, stop and split into a feature plan instead of silently marking it planned.
- If OpenAPI generation already exists elsewhere, stop and integrate with it rather than adding a competing registry.
