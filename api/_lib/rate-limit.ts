import type { VercelRequest, VercelResponse } from '@vercel/node';
import crypto from 'node:crypto';
import { sendJson } from './http';

export type RateLimitPolicy = {
  id: string;
  limit: number;
  windowMs: number;
};

export type RateLimitDecision = {
  allowed: boolean;
  limit: number;
  remaining: number;
  resetAt: number;
};

type Bucket = {
  count: number;
  resetAt: number;
};

type RateLimitKeyPart = string | number | boolean | null | undefined;

type ApplyRateLimitOptions = {
  keyParts?: RateLimitKeyPart[];
  cacheControl?: string;
};

export const RATE_LIMIT_POLICIES = {
  authLogin: { id: 'auth.login.post', limit: 10, windowMs: 60 * 1000 },
  authRegister: { id: 'auth.register.post', limit: 5, windowMs: 60 * 60 * 1000 },
  authMe: { id: 'auth.me.get', limit: 30, windowMs: 60 * 1000 },
  takedownRequest: { id: 'takedown-request.post', limit: 5, windowMs: 60 * 60 * 1000 },
  closureReport: { id: 'closure-report.post', limit: 20, windowMs: 60 * 60 * 1000 },
  communityPosts: { id: 'community.posts.post', limit: 10, windowMs: 60 * 60 * 1000 },
  communityComments: { id: 'community.comments.post', limit: 30, windowMs: 60 * 60 * 1000 },
  placeReactions: { id: 'v1.places.reactions.post', limit: 60, windowMs: 60 * 1000 },
} satisfies Record<string, RateLimitPolicy>;

export class FixedWindowRateLimiter {
  private buckets = new Map<string, Bucket>();

  constructor(private readonly maxBuckets = 10000) {}

  check(key: string, policy: RateLimitPolicy, now = Date.now()): RateLimitDecision {
    if (!policy.id || !Number.isInteger(policy.limit) || policy.limit < 1 || !Number.isInteger(policy.windowMs) || policy.windowMs < 1) {
      throw new Error('invalid rate limit policy');
    }

    const resetAt = Math.floor(now / policy.windowMs) * policy.windowMs + policy.windowMs;
    const bucket = this.buckets.get(key);
    if (!bucket || bucket.resetAt <= now) {
      this.ensureCapacity(now);
      this.buckets.set(key, { count: 1, resetAt });
      return { allowed: true, limit: policy.limit, remaining: policy.limit - 1, resetAt };
    }

    if (bucket.count >= policy.limit) {
      return { allowed: false, limit: policy.limit, remaining: 0, resetAt: bucket.resetAt };
    }

    bucket.count += 1;
    return { allowed: true, limit: policy.limit, remaining: policy.limit - bucket.count, resetAt: bucket.resetAt };
  }

  reset() {
    this.buckets.clear();
  }

  private ensureCapacity(now: number) {
    if (this.buckets.size < this.maxBuckets) return;
    for (const [key, bucket] of this.buckets.entries()) {
      if (bucket.resetAt <= now) {
        this.buckets.delete(key);
      }
    }
    while (this.buckets.size >= this.maxBuckets) {
      const oldestKey = this.buckets.keys().next().value;
      if (!oldestKey) break;
      this.buckets.delete(oldestKey);
    }
  }
}

const defaultLimiter = new FixedWindowRateLimiter();

function headerValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function serverObservedBoundary(req: VercelRequest) {
  const forwardedFor = headerValue(req.headers['x-forwarded-for']);
  const ip = forwardedFor?.split(',')[0]?.trim() || req.socket?.remoteAddress || 'unknown';
  const userAgent = headerValue(req.headers['user-agent']) || '';
  return `ip:${ip}\nua:${userAgent}`;
}

function normalizeKeyPart(part: RateLimitKeyPart) {
  if (part === null || part === undefined) return undefined;
  const normalized = String(part).trim();
  return normalized || undefined;
}

function rateLimitKey(req: VercelRequest, policy: RateLimitPolicy, keyParts: RateLimitKeyPart[]) {
  const material = [policy.id, serverObservedBoundary(req), ...keyParts.map(normalizeKeyPart).filter(Boolean)].join('\0');
  return crypto.createHash('sha256').update(material).digest('hex');
}

function setRateLimitHeaders(res: VercelResponse, decision: RateLimitDecision, now: number) {
  res.setHeader('X-RateLimit-Limit', String(decision.limit));
  res.setHeader('X-RateLimit-Remaining', String(Math.max(0, decision.remaining)));
  res.setHeader('X-RateLimit-Reset', String(Math.ceil(decision.resetAt / 1000)));
  if (!decision.allowed) {
    res.setHeader('Retry-After', String(Math.max(1, Math.ceil((decision.resetAt - now) / 1000))));
  }
}

// Best-effort only: this in-memory state is scoped to a warm Node/Vercel
// function instance. Use edge/WAF or shared KV/Redis for global enforcement.
export function applyRateLimit(
  req: VercelRequest,
  res: VercelResponse,
  policy: RateLimitPolicy,
  options: ApplyRateLimitOptions = {},
) {
  const now = Date.now();
  const decision = defaultLimiter.check(rateLimitKey(req, policy, options.keyParts ?? []), policy, now);
  setRateLimitHeaders(res, decision, now);
  if (decision.allowed) {
    return true;
  }
  sendJson(res, 429, { error: 'rate_limited' }, options.cacheControl ?? false);
  return false;
}

export function _resetRateLimiterForTest() {
  if (process.env.NODE_ENV !== 'test' && !process.env.VITEST) {
    throw new Error('rate limit reset is only available in tests');
  }
  defaultLimiter.reset();
}
