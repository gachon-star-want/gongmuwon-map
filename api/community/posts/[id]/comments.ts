import type { VercelRequest, VercelResponse } from '@vercel/node';
import { readQuery, writeQuery } from '../../../_lib/db';
import { parseBody, sendJson, uuidParam } from '../../../_lib/http';
import { getCurrentUser } from '../../../_lib/auth';
import { RATE_LIMIT_POLICIES, applyRateLimit } from '../../../_lib/rate-limit';
import { guardPrivateWriteRoute } from '../../../_lib/route';
import { sendTurnstileError, turnstileTokenFromBody, verifyTurnstileToken } from '../../../_lib/turnstile';

const COMMUNITY_COMMENTS_ALLOW_METHODS = 'GET, HEAD, POST, OPTIONS';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const method = req.method === 'HEAD' ? 'GET' : req.method;
  if (method === 'OPTIONS') {
    guardPrivateWriteRoute(req, res, { allowMethods: COMMUNITY_COMMENTS_ALLOW_METHODS });
    return;
  }

  try {
    const postId = uuidParam(req.query.id);
    if (postId === undefined) {
      sendJson(res, 400, { error: 'missing_post_id' });
      return;
    }
    if (postId === null) {
      sendJson(res, 400, { error: 'invalid_post_id' });
      return;
    }

    if (method === 'GET') {
      const { rows } = await readQuery(
        `
        SELECT id, post_id, body, author_handle, created_at
        FROM public.community_comments_public
        WHERE post_id = $1
        ORDER BY created_at ASC
      `,
        [postId],
      );
      sendJson(res, 200, { items: rows }, false, true);
      return;
    }

    if (method === 'POST') {
      if (!guardPrivateWriteRoute(req, res, { allowMethods: COMMUNITY_COMMENTS_ALLOW_METHODS })) {
        return;
      }
      const user = await getCurrentUser(req);
      if (!applyRateLimit(req, res, RATE_LIMIT_POLICIES.communityComments, { keyParts: user ? ['user', user.id] : [] })) {
        return;
      }
      if (!user) {
        sendJson(res, 401, { error: 'login_required' });
        return;
      }
      const parsedBody = parseBody(req);
      const turnstile = await verifyTurnstileToken(req, turnstileTokenFromBody(parsedBody), 'community_comment');
      if (turnstile.ok === false) {
        sendTurnstileError(res, turnstile);
        return;
      }
      const body = String(parsedBody.body || '').trim();
      if (!body || body.length > 1000) {
        sendJson(res, 400, { error: 'invalid_comment' });
        return;
      }
      const exists = await writeQuery('SELECT id FROM public.community_posts WHERE id = $1 AND hidden_at IS NULL AND deleted_at IS NULL', [
        postId,
      ]);
      if (!exists.rows[0]) {
        sendJson(res, 404, { error: 'not_found' });
        return;
      }
      const { rows } = await writeQuery(
        `
        INSERT INTO public.community_comments (post_id, author_id, body)
        VALUES ($1, $2, $3)
        RETURNING id
      `,
        [postId, user.id, body],
      );
      sendJson(res, 201, { id: rows[0].id });
      return;
    }

    res.setHeader('Allow', 'GET, HEAD, POST, OPTIONS');
    sendJson(res, 405, { error: 'method_not_allowed' });
  } catch (error) {
    console.error('communityComments:', error);
    sendJson(res, 500, { error: 'internal_error' });
  }
}
