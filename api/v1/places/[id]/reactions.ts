import type { VercelRequest, VercelResponse } from '@vercel/node';
import { writeQuery } from '../../../_lib/db';
import { getCurrentUser } from '../../../_lib/auth';
import { parseBody, sendJson, stringParam } from '../../../_lib/http';

type Reaction = 'like' | 'dislike';

async function summary(placeId: string, userId?: string) {
  const counts = await writeQuery<{ like_count: number; dislike_count: number }>(
    `
    SELECT COALESCE(like_count, 0)::integer AS like_count,
           COALESCE(dislike_count, 0)::integer AS dislike_count
    FROM public.place_reaction_counts
    WHERE place_id = $1
    UNION ALL
    SELECT 0, 0
    WHERE NOT EXISTS (SELECT 1 FROM public.place_reaction_counts WHERE place_id = $1)
    LIMIT 1
  `,
    [placeId],
  );
  let userReaction: Reaction | null = null;
  if (userId) {
    const user = await writeQuery<{ reaction: Reaction }>(
      'SELECT reaction FROM public.place_reactions WHERE place_id = $1 AND user_id = $2 LIMIT 1',
      [placeId, userId],
    );
    userReaction = user.rows[0]?.reaction ?? null;
  }
  return {
    like_count: counts.rows[0]?.like_count ?? 0,
    dislike_count: counts.rows[0]?.dislike_count ?? 0,
    user_reaction: userReaction,
  };
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const method = req.method === 'HEAD' ? 'GET' : req.method;
  if (method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Methods', 'GET, HEAD, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.status(204).end();
    return;
  }

  try {
    const placeId = stringParam(req.query.id);
    if (!placeId) {
      sendJson(res, 400, { error: 'missing_place_id' });
      return;
    }
    const user = await getCurrentUser(req);

    if (method === 'GET') {
      sendJson(res, 200, await summary(placeId, user?.id), false, true);
      return;
    }

    if (method === 'POST') {
      if (!user) {
        sendJson(res, 401, { error: 'login_required' });
        return;
      }
      const reaction = parseBody(req).reaction;
      if (reaction === null || reaction === '') {
        await writeQuery('DELETE FROM public.place_reactions WHERE place_id = $1 AND user_id = $2', [placeId, user.id]);
        sendJson(res, 200, await summary(placeId, user.id));
        return;
      }
      if (reaction !== 'like' && reaction !== 'dislike') {
        sendJson(res, 400, { error: 'invalid_reaction' });
        return;
      }
      await writeQuery(
        `
        INSERT INTO public.place_reactions (place_id, user_id, reaction)
        VALUES ($1, $2, $3)
        ON CONFLICT (place_id, user_id)
        DO UPDATE SET reaction = EXCLUDED.reaction, updated_at = now()
      `,
        [placeId, user.id, reaction],
      );
      sendJson(res, 200, await summary(placeId, user.id));
      return;
    }

    res.setHeader('Allow', 'GET, HEAD, POST, OPTIONS');
    sendJson(res, 405, { error: 'method_not_allowed' });
  } catch {
    sendJson(res, 500, { error: 'internal_error' });
  }
}

