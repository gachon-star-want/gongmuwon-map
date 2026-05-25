import type { VercelRequest, VercelResponse } from '@vercel/node';
import { readQuery } from '../../../_lib/db';
import { publicReadRoute } from '../../../_lib/route';
import { numberParam, stringParam } from '../../../_lib/http';

export default publicReadRoute(async function handler(req: VercelRequest, res: VercelResponse) {
  const id = stringParam(req.query.id);
  if (!id) {
    return { status: 400, body: { error: 'missing_place_id' } };
  }
  const limit = Math.min(Math.max(numberParam(req.query.limit, 100), 1), 500);
  const { rows } = await readQuery(
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
  return rows;
}, { cache: true });
