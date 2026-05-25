import { writeQuery } from './_lib/db';
import { parseBody } from './_lib/http';
import { privateWriteRoute } from './_lib/route';

export default privateWriteRoute(async function handler({ req }) {
  const body = parseBody(req);
  const placeId = String(body.place_id || '');
  const reason = typeof body.reason === 'string' ? body.reason.trim().slice(0, 2000) : '';
  const email = typeof body.email === 'string' ? body.email.trim().slice(0, 320) : null;
  if (!placeId || reason.length < 10) {
    return { status: 400, body: { error: 'invalid_request' } };
  }

  const { rows } = await writeQuery(
    'SELECT public.request_takedown($1::uuid, $2::text, $3::text) AS result',
    [placeId, reason, email],
  );
  return rows[0]?.result ?? { ok: true };
});
