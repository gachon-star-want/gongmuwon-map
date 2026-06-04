import { writeQuery } from './_lib/db';
import { parseBody, reporterFingerprint, uuidParam } from './_lib/http';
import { RATE_LIMIT_POLICIES, applyRateLimit } from './_lib/rate-limit';
import { privateWriteRoute } from './_lib/route';
import { turnstileTokenFromBody, verifyTurnstileToken } from './_lib/turnstile';

export default privateWriteRoute(async function handler({ req, res }) {
  if (!applyRateLimit(req, res, RATE_LIMIT_POLICIES.closureReport)) {
    return;
  }
  const body = parseBody(req);
  const turnstile = await verifyTurnstileToken(req, turnstileTokenFromBody(body), 'closure_report');
  if (turnstile.ok === false) {
    return { status: turnstile.status, body: { error: turnstile.error } };
  }
  const placeId = uuidParam(body.place_id);
  if (placeId === undefined) {
    return { status: 400, body: { error: 'missing_place_id' } };
  }
  if (placeId === null) {
    return { status: 400, body: { error: 'invalid_place_id' } };
  }

  const fp = reporterFingerprint(req);
  const note = typeof body.note === 'string' ? body.note.slice(0, 1000) : null;
  const { rows } = await writeQuery(
    'SELECT public.report_closure($1::uuid, $2::text, $3::text) AS result',
    [placeId, fp, note],
  );
  return rows[0]?.result ?? { ok: true };
});
