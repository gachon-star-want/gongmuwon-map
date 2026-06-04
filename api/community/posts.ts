import type { VercelRequest, VercelResponse } from '@vercel/node';
import { readQuery, writeQuery } from '../_lib/db';
import { numberParam, parseBody, sendJson, stringParam } from '../_lib/http';
import { getCurrentUser } from '../_lib/auth';
import { RATE_LIMIT_POLICIES, applyRateLimit } from '../_lib/rate-limit';
import { guardPrivateWriteRoute, privateWriteRoute } from '../_lib/route';
import { turnstileTokenFromBody, verifyTurnstileToken } from '../_lib/turnstile';

const ALLOWED_CATEGORIES = new Set(['free', 'question', 'meetup', 'tip', 'notice']);
const COMMUNITY_POSTS_ALLOW_METHODS = 'GET, HEAD, POST, OPTIONS';

function cleanCategory(value?: string) {
  return value && ALLOWED_CATEGORIES.has(value) ? value : undefined;
}

const handlePost = privateWriteRoute(async ({ req, res }) => {
  const user = await getCurrentUser(req);
  if (!applyRateLimit(req, res, RATE_LIMIT_POLICIES.communityPosts, { keyParts: user ? ['user', user.id] : [] })) {
    return;
  }
  if (!user) {
    return { status: 401, body: { error: 'login_required' } };
  }
  const body = parseBody(req);
  const turnstile = await verifyTurnstileToken(req, turnstileTokenFromBody(body), 'community_post');
  if (turnstile.ok === false) {
    return { status: turnstile.status, body: { error: turnstile.error } };
  }
  const title = String(body.title || '').trim();
  const postBody = String(body.body || '').trim();
  const category = cleanCategory(String(body.category || 'free')) ?? 'free';
  if (title.length < 2 || title.length > 80 || postBody.length < 1 || postBody.length > 4000) {
    return { status: 400, body: { error: 'invalid_post' } };
  }
  const { rows } = await writeQuery(
    `
    INSERT INTO public.community_posts (author_id, category, title, body)
    VALUES ($1, $2, $3, $4)
    RETURNING id
  `,
    [user.id, category, title, postBody],
  );
  return { status: 201, body: { id: rows[0].id } };
});

async function handleGet(req: VercelRequest, res: VercelResponse) {
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
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const method = req.method === 'HEAD' ? 'GET' : req.method;

  if (method === 'OPTIONS') {
    guardPrivateWriteRoute(req, res, { allowMethods: COMMUNITY_POSTS_ALLOW_METHODS });
    return;
  }

  try {
    if (method === 'GET') {
      await handleGet(req, res);
      return;
    }

    if (method === 'POST') {
      await handlePost(req, res);
      return;
    }
  } catch (error) {
    console.error('communityPosts:', error);
    sendJson(res, 500, { error: 'internal_error' });
    return;
  }

  res.setHeader('Allow', 'GET, HEAD, POST, OPTIONS');
  sendJson(res, 405, { error: 'method_not_allowed' });
}
