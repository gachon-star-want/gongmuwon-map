import type { VercelRequest, VercelResponse } from '@vercel/node';
import { readQuery, writeQuery } from '../_lib/db';
import { numberParam, parseBody, sendJson, stringParam } from '../_lib/http';
import { getCurrentUser } from '../_lib/auth';
import { RATE_LIMIT_POLICIES, applyRateLimit } from '../_lib/rate-limit';
import { guardPrivateWriteRoute } from '../_lib/route';
import { sendTurnstileError, turnstileTokenFromBody, verifyTurnstileToken } from '../_lib/turnstile';

const ALLOWED_CATEGORIES = new Set(['free', 'question', 'meetup', 'tip', 'notice']);
const COMMUNITY_POSTS_ALLOW_METHODS = 'GET, HEAD, POST, OPTIONS';

function cleanCategory(value?: string) {
  return value && ALLOWED_CATEGORIES.has(value) ? value : undefined;
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const method = req.method === 'HEAD' ? 'GET' : req.method;
  if (method === 'OPTIONS') {
    guardPrivateWriteRoute(req, res, { allowMethods: COMMUNITY_POSTS_ALLOW_METHODS });
    return;
  }

  try {
    if (method === 'GET') {
      const limit = Math.min(Math.max(numberParam(req.query.limit, 30), 1), 50);
      const category = cleanCategory(stringParam(req.query.category));
      const values: unknown[] = [limit];
      const where = category ? 'WHERE category = $2' : '';
      if (category) values.push(category);
      const { rows } = await readQuery(
        `
        SELECT id, category, title, body, author_handle, comment_count, created_at, updated_at, last_comment_at
        FROM public.community_posts_public
        ${where}
        ORDER BY COALESCE(last_comment_at, created_at) DESC, created_at DESC
        LIMIT $1
      `,
        values,
      );
      sendJson(res, 200, { items: rows }, false, true);
      return;
    }

    if (method === 'POST') {
      if (!guardPrivateWriteRoute(req, res, { allowMethods: COMMUNITY_POSTS_ALLOW_METHODS })) {
        return;
      }
      const user = await getCurrentUser(req);
      if (!applyRateLimit(req, res, RATE_LIMIT_POLICIES.communityPosts, { keyParts: user ? ['user', user.id] : [] })) {
        return;
      }
      if (!user) {
        sendJson(res, 401, { error: 'login_required' });
        return;
      }
      const body = parseBody(req);
      const turnstile = await verifyTurnstileToken(req, turnstileTokenFromBody(body), 'community_post');
      if (turnstile.ok === false) {
        sendTurnstileError(res, turnstile);
        return;
      }
      const title = String(body.title || '').trim();
      const postBody = String(body.body || '').trim();
      const category = cleanCategory(String(body.category || 'free')) ?? 'free';
      if (title.length < 2 || title.length > 80 || postBody.length < 1 || postBody.length > 4000) {
        sendJson(res, 400, { error: 'invalid_post' });
        return;
      }
      const { rows } = await writeQuery(
        `
        INSERT INTO public.community_posts (author_id, category, title, body)
        VALUES ($1, $2, $3, $4)
        RETURNING id
      `,
        [user.id, category, title, postBody],
      );
      sendJson(res, 201, { id: rows[0].id });
      return;
    }

    res.setHeader('Allow', 'GET, HEAD, POST, OPTIONS');
    sendJson(res, 405, { error: 'method_not_allowed' });
  } catch (error) {
    console.error('communityPosts:', error);
    sendJson(res, 500, { error: 'internal_error' });
  }
}
