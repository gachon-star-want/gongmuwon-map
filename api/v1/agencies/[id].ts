import type { VercelRequest, VercelResponse } from '@vercel/node';
import { readQuery } from '../../_lib/db';
import { publicReadRoute } from '../../_lib/route';
import { stringParam } from '../../_lib/http';

export default publicReadRoute(async function handler(req: VercelRequest, res: VercelResponse) {
  const id = stringParam(req.query.id);
  if (!id) {
    return { status: 400, body: { error: 'missing_agency_id' } };
  }
  const { rows } = await readQuery('SELECT * FROM public.agencies_public WHERE id = $1 LIMIT 1', [id]);
  if (!rows[0]) {
    return { status: 404, body: { error: 'not_found' } };
  }
  return rows[0];
}, { cache: true });
