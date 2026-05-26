import type { VercelRequest, VercelResponse } from '@vercel/node';
import { getCurrentUser } from '../_lib/auth';
import { sendJson } from '../_lib/http';

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
    sendJson(res, 200, { user: await getCurrentUser(req) });
  } catch {
    sendJson(res, 500, { error: 'internal_error' });
  }
}

