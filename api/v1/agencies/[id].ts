import type { VercelRequest, VercelResponse } from '@vercel/node';
import { query } from '../../_lib/db';
import { methodGuard, sendJson, stringParam } from '../../_lib/http';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (!methodGuard(req, res, ['GET'])) return;
  const id = stringParam(req.query.id);
  if (!id) {
    sendJson(res, 400, { error: 'missing_agency_id' });
    return;
  }
  const { rows } = await query('SELECT * FROM public.agencies_public WHERE id = $1 LIMIT 1', [id]);
  if (!rows[0]) {
    sendJson(res, 404, { error: 'not_found' });
    return;
  }
  sendJson(res, 200, rows[0], true);
}
