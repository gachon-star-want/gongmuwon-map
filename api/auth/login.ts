import type { VercelRequest, VercelResponse } from '@vercel/node';
import { writeQuery } from '../_lib/db';
import { parseBody, sendJson } from '../_lib/http';
import { createSession, normalizeHandle, verifyPassword } from '../_lib/auth';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.status(204).end();
    return;
  }
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST, OPTIONS');
    sendJson(res, 405, { error: 'method_not_allowed' });
    return;
  }

  try {
    const body = parseBody(req);
    const handle = String(body.handle || '');
    const password = String(body.password || '');
    const { rows } = await writeQuery<{
      id: string;
      handle: string;
      role: string;
      created_at: string;
      password_hash: string;
      password_salt: string;
    }>(
      `
      SELECT id, handle, role, created_at, password_hash, password_salt
      FROM public.app_users
      WHERE handle_normalized = $1
        AND deleted_at IS NULL
      LIMIT 1
    `,
      [normalizeHandle(handle)],
    );
    const user = rows[0];
    if (!user || !(await verifyPassword(password, user.password_salt, user.password_hash))) {
      sendJson(res, 401, { error: 'invalid_credentials' });
      return;
    }
    await writeQuery('UPDATE public.app_users SET last_login_at = now() WHERE id = $1', [user.id]);
    await createSession(res, user.id);
    sendJson(res, 200, { user: { id: user.id, handle: user.handle, role: user.role, created_at: user.created_at } });
  } catch {
    sendJson(res, 500, { error: 'internal_error' });
  }
}

