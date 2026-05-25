import type { VercelRequest, VercelResponse } from '@vercel/node';
import { writeQuery } from './_lib/db';
import { parseBody, reporterFingerprint } from './_lib/http';
import { privateWriteRoute } from './_lib/route';

export default privateWriteRoute(async function handler(req: VercelRequest, res: VercelResponse) {
  const body = parseBody(req);
  const placeId = String(body.place_id || '');
  if (!placeId) {
    return { status: 400, body: { error: 'missing_place_id' } };
  }

  const fp = reporterFingerprint(req, body.reporter_fp);
  const note = typeof body.note === 'string' ? body.note.slice(0, 1000) : null;
  const { rows } = await writeQuery(
    'SELECT public.report_closure($1::uuid, $2::text, $3::text) AS result',
    [placeId, fp, note],
  );
  return rows[0]?.result ?? { ok: true };
});
