import type { VercelRequest, VercelResponse } from '@vercel/node';
import { sendJson } from './http';

type TurnstileOutcome =
  | { ok: true }
  | {
      ok: false;
      status: number;
      error: 'turnstile_required' | 'turnstile_not_configured' | 'turnstile_unavailable' | 'turnstile_failed';
    };

type SiteverifyResponse = {
  success?: boolean;
  action?: string;
  'error-codes'?: string[];
};

const SITEVERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';
const MAX_TOKEN_LENGTH = 2048;

function headerValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function clientIp(req: VercelRequest) {
  const forwardedFor = headerValue(req.headers['x-forwarded-for']);
  return forwardedFor?.split(',')[0]?.trim() || req.socket.remoteAddress || undefined;
}

export function turnstileTokenFromBody(body: unknown) {
  if (!body || typeof body !== 'object') {
    return '';
  }
  const record = body as Record<string, unknown>;
  const token = record.turnstile_token ?? record.turnstileToken ?? record['cf-turnstile-response'];
  return typeof token === 'string' ? token.trim() : '';
}

export async function verifyTurnstileToken(req: VercelRequest, token: string, expectedAction: string): Promise<TurnstileOutcome> {
  const secret = process.env.TURNSTILE_SECRET_KEY?.trim();
  if (!secret) {
    return { ok: false, status: 503, error: 'turnstile_not_configured' };
  }
  if (!token || token.length > MAX_TOKEN_LENGTH) {
    return { ok: false, status: 400, error: 'turnstile_required' };
  }

  const form = new URLSearchParams({ secret, response: token });
  const ip = clientIp(req);
  if (ip) {
    form.set('remoteip', ip);
  }

  try {
    const response = await fetch(process.env.TURNSTILE_SITEVERIFY_URL || SITEVERIFY_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    });
    if (!response.ok) {
      return { ok: false, status: 503, error: 'turnstile_unavailable' };
    }
    const result = (await response.json()) as SiteverifyResponse;
    if (!result.success || result.action !== expectedAction) {
      return { ok: false, status: 403, error: 'turnstile_failed' };
    }
    return { ok: true };
  } catch {
    return { ok: false, status: 503, error: 'turnstile_unavailable' };
  }
}

export function sendTurnstileError(res: VercelResponse, outcome: Exclude<TurnstileOutcome, { ok: true }>) {
  sendJson(res, outcome.status, { error: outcome.error });
}
