# plan3b.md — Public Route Policy Tests

## Execution Snapshot

- **Status**: Observed as implemented in the current worktree; final verification/checkpoint still required.
- **Resume point**: Confirm route policy tests cover method, CORS, cache, and DB-role behavior, then mark complete in `STATUS.md`.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Add a small test harness for the public/private route policy introduced in `plan3.md`. This plan exists because method, CORS, cache, and DB-role rules are security-sensitive and must not remain verified only by grep.

## Prerequisites

- `plan3.md` is complete.

## Read First

- `api/_lib/route.ts`
- `api/_lib/db.ts`
- `api/_lib/http.ts`
- `api/v1/places.ts`
- `api/closure-report.ts`
- `api/takedown-request.ts`
- `package.json`
- `apps/web/package.json`

## Files To Touch

Primary:

- `api/_lib/route.test.ts` (new)
- `api/_lib/db.test.ts` (new if DB helpers are testable without network)
- `package.json`

Do not rewrite API route implementations in this plan except to export pure helpers needed for tests.

## Test Harness Decision

Use the existing workspace Vitest dependency from `apps/web`; do not add a second test framework. Add a root package script:

```json
"test:api": "npm --workspace apps/web exec vitest run ../../api/_lib/*.test.ts"
```

The tests must use hand-rolled mock `req`/`res` objects. Do not start a real HTTP server and do not connect to Postgres.

## Required Tests

`api/_lib/route.test.ts`:

- `publicReadRoute` accepts `GET`, `HEAD`, and `OPTIONS`.
- `publicReadRoute` rejects `POST` with `405`.
- `publicReadRoute` sets `Access-Control-Allow-Origin: *`.
- `publicReadRoute` applies the route cache option and never sets cache for errors unless the helper intentionally does so.
- `privateWriteRoute` accepts `POST` and `OPTIONS`.
- `privateWriteRoute` rejects `GET` with `405`.
- `privateWriteRoute` allows missing `Origin`.
- `privateWriteRoute` allows `PUBLIC_SITE_ORIGIN`.
- `privateWriteRoute` allows comma-separated `PUBLIC_WRITE_ORIGIN`.
- `privateWriteRoute` rejects an unapproved `Origin` with `403`.
- `privateWriteRoute` never sets public cache.

`api/_lib/db.test.ts`:

- `readPool` throws when `DATABASE_URL_READONLY` is missing.
- `readPool` does not fall back to `DATABASE_URL`.
- `writePool` throws when `DATABASE_URL` is missing.
- `readQuery` calls the read pool and `writeQuery` calls the write pool. Use dependency injection or exported reset hooks; do not connect to a real database.

## Implementation Notes

- If singleton pools make DB helper tests hard, add a test-only exported `_resetPoolsForTest()` and an injectable pool factory:
  ```ts
  export function _setPoolFactoryForTest(factory: (url: string, max: number) => Pool): void;
  ```
  Keep the test hook private by naming and documentation; route code must not call it.
- Preserve current production imports for route handlers.

## Tests

Run:

```bash
npm run test:api
npm run build
```

Optional regression grep:

```bash
rg -n "DATABASE_URL_READONLY \\|\\| process\\.env\\.DATABASE_URL|Access-Control-Allow-Origin', '\\*'|query\\(" api
```

## Acceptance Criteria

- Route policy behavior is tested without a network server.
- Read DB helpers cannot silently use the write URL.
- Write routes cannot accidentally inherit public wildcard CORS or cache.

## STOP Conditions

- If Vitest cannot run tests outside `apps/web`, stop and add a root-level test plan instead of moving API code under the web app.
- If testing requires real DB credentials, stop and refactor helpers to allow pure unit tests.
