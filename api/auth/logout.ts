import type { VercelRequest, VercelResponse } from '@vercel/node';
import { destroySession } from '../_lib/auth';
import { sendJson } from '../_lib/http';

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
    await destroySession(req, res);
    sendJson(res, 200, { ok: true });
  } catch {
    sendJson(res, 500, { error: 'internal_error' });
  }
}

