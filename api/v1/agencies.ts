import type { VercelRequest, VercelResponse } from '@vercel/node';
import { query } from '../_lib/db';
import { methodGuard, sendJson } from '../_lib/http';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (!methodGuard(req, res, ['GET'])) return;
  const { rows } = await query(
    `
    SELECT id, name, short_name, kind, parent_region, sub_region, homepage,
      visit_count, place_count, last_visit_at
    FROM public.agencies_public
    ORDER BY kind, sub_region NULLS FIRST, short_name
    `,
  );
  sendJson(res, 200, rows, true);
}
