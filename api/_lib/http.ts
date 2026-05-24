import type { VercelRequest, VercelResponse } from '@vercel/node';
import crypto from 'node:crypto';

export function sendJson(res: VercelResponse, status: number, body: unknown, cache = false) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  if (cache) {
    res.setHeader('Cache-Control', 'public, s-maxage=300, stale-while-revalidate=600');
  }
  res.status(status).json(body);
}

export function methodGuard(req: VercelRequest, res: VercelResponse, methods: string[]) {
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', methods.join(', '));
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.status(204).end();
    return false;
  }
  if (!req.method || !methods.includes(req.method)) {
    res.setHeader('Allow', methods.join(', '));
    sendJson(res, 405, { error: 'method_not_allowed' });
    return false;
  }
  return true;
}

export function numberParam(value: unknown, fallback: number) {
  const raw = Array.isArray(value) ? value[0] : value;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function stringParam(value: unknown) {
  const raw = Array.isArray(value) ? value[0] : value;
  return typeof raw === 'string' ? raw : undefined;
}

export function parseBody(req: VercelRequest) {
  if (typeof req.body === 'string') {
    return req.body ? JSON.parse(req.body) : {};
  }
  return req.body || {};
}

export function reporterFingerprint(req: VercelRequest, provided?: string) {
  if (provided && provided.length >= 12) {
    return provided.slice(0, 128);
  }
  const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress || '';
  const ua = req.headers['user-agent'] || '';
  return crypto.createHash('sha256').update(`${ip}:${ua}`).digest('hex');
}

export function requireCronSecret(req: VercelRequest, res: VercelResponse) {
  const secret = process.env.CRON_SECRET;
  if (!secret) {
    return true;
  }
  const header = req.headers.authorization || '';
  if (header === `Bearer ${secret}`) {
    return true;
  }
  sendJson(res, 401, { error: 'unauthorized' });
  return false;
}
