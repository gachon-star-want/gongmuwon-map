import type { VercelRequest, VercelResponse } from '@vercel/node';
import { writeQuery } from '../_lib/db';
import { parseBody, sendJson } from '../_lib/http';
import { createSession, hashPassword, normalizeHandle, validateHandle, validatePassword } from '../_lib/auth';

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
    const handle = String(body.handle || '').trim();
    const password = String(body.password || '');
    if (!validateHandle(handle)) {
      sendJson(res, 400, { error: 'invalid_handle' });
      return;
    }
    if (!validatePassword(password)) {
      sendJson(res, 400, { error: 'invalid_password' });
      return;
    }

    const passwordResult = await hashPassword(password);
    const { rows } = await writeQuery<{ id: string; handle: string; role: string; created_at: string }>(
      `
      INSERT INTO public.app_users (handle, handle_normalized, password_hash, password_salt)
      VALUES ($1, $2, $3, $4)
      RETURNING id, handle, role, created_at
    `,
      [handle, normalizeHandle(handle), passwordResult.hash, passwordResult.salt],
    );
    await createSession(res, rows[0].id);
    sendJson(res, 201, { user: rows[0] });
  } catch (error) {
    if ((error as { code?: string }).code === '23505') {
      sendJson(res, 409, { error: 'handle_taken' });
      return;
    }
    sendJson(res, 500, { error: 'internal_error' });
  }
}

