import type { VercelRequest, VercelResponse } from '@vercel/node';
import { query } from './_lib/db';
import { methodGuard, parseBody, reporterFingerprint, sendJson } from './_lib/http';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (!methodGuard(req, res, ['POST'])) return;
  const body = parseBody(req);
  const placeId = String(body.place_id || '');
  if (!placeId) {
    sendJson(res, 400, { error: 'missing_place_id' });
    return;
  }

  const fp = reporterFingerprint(req, body.reporter_fp);
  const note = typeof body.note === 'string' ? body.note.slice(0, 1000) : null;
  const { rows } = await query(
    'SELECT public.report_closure($1::uuid, $2::text, $3::text) AS result',
    [placeId, fp, note],
    'write',
  );
  sendJson(res, 200, rows[0]?.result ?? { ok: true });
}
