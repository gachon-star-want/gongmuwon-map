import type { VercelRequest, VercelResponse } from '@vercel/node';
import { query } from './_lib/db';
import { methodGuard, parseBody, sendJson } from './_lib/http';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (!methodGuard(req, res, ['POST'])) return;
  const body = parseBody(req);
  const placeId = String(body.place_id || '');
  const reason = typeof body.reason === 'string' ? body.reason.trim().slice(0, 2000) : '';
  const email = typeof body.email === 'string' ? body.email.trim().slice(0, 320) : null;
  if (!placeId || reason.length < 10) {
    sendJson(res, 400, { error: 'invalid_request' });
    return;
  }

  const { rows } = await query(
    'SELECT public.request_takedown($1::uuid, $2::text, $3::text) AS result',
    [placeId, reason, email],
    'write',
  );
  sendJson(res, 200, rows[0]?.result ?? { ok: true });
}
