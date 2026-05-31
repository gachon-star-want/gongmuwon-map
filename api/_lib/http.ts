import type { VercelRequest, VercelResponse } from '@vercel/node';
import crypto from 'node:crypto';

export function sendJson(
  res: VercelResponse,
  status: number,
  body: unknown,
  cache: boolean | string = false,
  cors = false,
) {
  if (cors) {
    res.setHeader('Access-Control-Allow-Origin', '*');
  }
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  if (cache) {
    res.setHeader('Cache-Control', cache === true ? 'public, s-maxage=300, stale-while-revalidate=600' : cache);
  }
  res.status(status).json(body);
}

export function methodGuard(req: VercelRequest, res: VercelResponse, methods: string[]) {
  const requestMethod = req.method === 'HEAD' && methods.includes('GET') ? 'GET' : req.method;
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Methods', methods.join(', '));
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.status(204).end();
    return false;
  }
  if (!requestMethod || !methods.includes(requestMethod)) {
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

function headerValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export function reporterFingerprint(req: VercelRequest) {
  const forwardedFor = headerValue(req.headers['x-forwarded-for']);
  const ip = forwardedFor?.split(',')[0]?.trim() || req.socket.remoteAddress || '';
  const ua = headerValue(req.headers['user-agent']) || '';
  return crypto.createHash('sha256').update(`${ip}:${ua}`).digest('hex');
}

export function requireCronSecret(req: VercelRequest, res: VercelResponse) {
  const secret = process.env.CRON_SECRET?.trim();
  if (!secret) {
    sendJson(res, 503, { error: 'cron_secret_not_configured' });
    return false;
  }
  const authorization = req.headers.authorization;
  const header = Array.isArray(authorization) ? '' : authorization || '';
  if (timingSafeStringEqual(header, `Bearer ${secret}`)) {
    return true;
  }
  sendJson(res, 401, { error: 'unauthorized' });
  return false;
}

function timingSafeStringEqual(a: string, b: string) {
  const aBuffer = Buffer.from(a);
  const bBuffer = Buffer.from(b);
  if (aBuffer.length === bBuffer.length) {
    return crypto.timingSafeEqual(aBuffer, bBuffer);
  }
  const length = Math.max(aBuffer.length, bBuffer.length);
  const aPadded = Buffer.alloc(length);
  const bPadded = Buffer.alloc(length);
  aBuffer.copy(aPadded);
  bBuffer.copy(bPadded);
  crypto.timingSafeEqual(aPadded, bPadded);
  return false;
}
