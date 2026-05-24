import type { VercelRequest, VercelResponse } from '@vercel/node';
import { query } from '../../../_lib/db';
import { methodGuard, numberParam, sendJson, stringParam } from '../../../_lib/http';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (!methodGuard(req, res, ['GET'])) return;
  const id = stringParam(req.query.id);
  if (!id) {
    sendJson(res, 400, { error: 'missing_place_id' });
    return;
  }
  const limit = Math.min(Math.max(numberParam(req.query.limit, 100), 1), 500);
  const { rows } = await query(
    `
    SELECT id, place_id, agency_id, visit_date, amount, party_size, department_name,
      rank_label, representative, purpose, source_url, source_title
    FROM public.place_visits_public
    WHERE place_id = $1
    ORDER BY visit_date DESC
    LIMIT $2
    `,
    [id, limit],
  );
  sendJson(res, 200, rows, true);
}
