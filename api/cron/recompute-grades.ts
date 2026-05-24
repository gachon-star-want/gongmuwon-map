import type { VercelRequest, VercelResponse } from '@vercel/node';
import { query } from '../_lib/db';
import { methodGuard, requireCronSecret, sendJson } from '../_lib/http';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (!methodGuard(req, res, ['GET', 'POST'])) return;
  if (!requireCronSecret(req, res)) return;
  await query('SELECT public.recompute_grades()', [], 'write');
  sendJson(res, 200, { ok: true });
}
