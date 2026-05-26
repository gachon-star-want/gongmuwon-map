import type { VercelRequest, VercelResponse } from '@vercel/node';
import { readQuery } from '../../_lib/db';
import { sendJson, stringParam } from '../../_lib/http';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const method = req.method === 'HEAD' ? 'GET' : req.method;
  if (method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.status(204).end();
    return;
  }
  if (method !== 'GET') {
    res.setHeader('Allow', 'GET, HEAD, OPTIONS');
    sendJson(res, 405, { error: 'method_not_allowed' });
    return;
  }
  try {
    const id = stringParam(req.query.id);
    if (!id) {
      sendJson(res, 400, { error: 'missing_post_id' });
      return;
    }
    const { rows } = await readQuery(
      `
      SELECT id, category, title, body, author_handle, comment_count, created_at, updated_at, last_comment_at
      FROM public.community_posts_public
      WHERE id = $1
      LIMIT 1
    `,
      [id],
    );
    if (!rows[0]) {
      sendJson(res, 404, { error: 'not_found' });
      return;
    }
    sendJson(res, 200, rows[0], false, true);
  } catch {
    sendJson(res, 500, { error: 'internal_error' });
  }
}

