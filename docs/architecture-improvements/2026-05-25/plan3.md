# plan3.md — Public Route Policy And Read Module

## Execution Snapshot

- **Status**: Observed as implemented in the current worktree; final verification/checkpoint still required.
- **Resume point**: Confirm read/write route helpers and readonly DB behavior, then mark complete in `STATUS.md`.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Create a deep route policy Module so each Vercel route does not reimplement method, CORS, cache, DB role, and error behavior. Fix the current shallow Seam where `DATABASE_URL_READONLY` falls back to `DATABASE_URL`.

## Read First

- `docs/PUBLIC_API.md`
- `docs/adr/ADR-010-database-stack-migration.md`
- `api/_lib/db.ts`
- `api/_lib/http.ts`
- all files under `api/v1/`
- `api/closure-report.ts`
- `api/takedown-request.ts`

## Files To Touch

Primary:

- `api/_lib/db.ts`
- `api/_lib/http.ts`
- `api/_lib/route.ts` (new)
- `api/v1/*.ts`
- `api/v1/**/*.ts`
- `api/closure-report.ts`
- `api/takedown-request.ts`
- `docs/PUBLIC_API.md`

Do not change endpoint response fields except where plan1 already changed agency taxonomy.

## Target Interface

Add `api/_lib/route.ts`:

```ts
type RouteContext = {
  req: VercelRequest;
  res: VercelResponse;
};

type PublicReadOptions = {
  cache?: boolean | string;
};

export function publicReadRoute(
  handler: (ctx: RouteContext) => Promise<unknown>,
  options?: PublicReadOptions,
): (req: VercelRequest, res: VercelResponse) => Promise<void>;

export function privateWriteRoute(
  handler: (ctx: RouteContext) => Promise<unknown>,
): (req: VercelRequest, res: VercelResponse) => Promise<void>;
```

Add DB helpers:

```ts
export function readPool(): Pool;   // requires DATABASE_URL_READONLY
export function writePool(): Pool;  // requires DATABASE_URL
export async function readQuery<T>(...): Promise<QueryResult<T>>;
export async function writeQuery<T>(...): Promise<QueryResult<T>>;
```

`query(text, values, kind)` can remain temporarily for compatibility, but route code should move to `readQuery`/`writeQuery`.

## Policy Decisions

- Public read routes:
  - allowed methods: `GET`, `HEAD`, `OPTIONS`
  - CORS: `Access-Control-Allow-Origin: *`
  - DB: `DATABASE_URL_READONLY` only; no fallback
  - cache: route-specific public cache allowed
- Private write routes:
  - allowed methods: `POST`, `OPTIONS`
  - CORS: allow missing `Origin` (server-to-server or same-origin form posts), `PUBLIC_SITE_ORIGIN`, and comma-separated `PUBLIC_WRITE_ORIGIN` values if present; reject all other origins with `403` and set `Vary: Origin`
  - DB: `DATABASE_URL` only
  - cache: never public cache
- Error shape:
  - default: `{ "error": "internal_error" }`
  - preserve existing explicit 400/404 errors.

## Implementation Steps

1. Add strict `readPool`, `writePool`, `readQuery`, and `writeQuery`.
   - Before removing the fallback, verify deployment configuration:
     ```bash
     vercel env ls
     ```
     If Vercel env access is unavailable, patch the code but report `DATABASE_URL_READONLY` as a deployment blocker in the final note.
2. Add `publicReadRoute` and `privateWriteRoute` wrappers.
3. Convert these routes first:
   - `/api/v1/places`
   - `/api/v1/places/search`
   - `/api/v1/places/[id]`
   - `/api/v1/places/[id]/visits`
   - `/api/v1/agencies`
   - `/api/v1/agencies/[id]`
   - `/api/v1/regions`
   - `/api/v1/stats/summary`
4. Convert write routes:
   - `/api/closure-report`
   - `/api/takedown-request`
5. Keep `api/cron/recompute-grades.ts` separate because it has cron-secret policy.
6. Update `PUBLIC_API.md` to state that missing `DATABASE_URL_READONLY` is a deployment error, not a fallback.

## Tests

If a TypeScript route test harness does not exist, add lightweight unit tests only for pure helpers. Do not build a full HTTP server in this plan.

Minimum verification:

```bash
npm run build
rg -n "DATABASE_URL_READONLY \\|\\| process\\.env\\.DATABASE_URL|query\\(" api
rg -n "Access-Control-Allow-Origin', '\\*'" api
```

Expected after conversion:

- No readonly fallback.
- Wildcard CORS only inside public read policy helper.
- Raw `query(` usage only remains in cron or intentionally deferred files.

## Acceptance Criteria

- Read routes cannot use the write DB URL by accident.
- Write routes do not inherit public read cache/CORS behavior.
- Method/CORS/cache/error policy has one deep Module Interface.

## STOP Conditions

- If production currently lacks `DATABASE_URL_READONLY`, stop and report deployment config risk before removing fallback.
- If a public write route must support cross-origin requests, stop and add an ADR or explicit docs update before allowing wildcard CORS.
- If Vercel env inspection is impossible from the current environment, continue the code refactor but mark deployment as blocked until `DATABASE_URL_READONLY` is confirmed.
