import { beforeEach, describe, expect, it } from 'vitest';
import { FixedWindowRateLimiter, _resetRateLimiterForTest, applyRateLimit } from './rate-limit';

type MockResponse = {
  headers: Map<string, unknown>;
  statusCode?: number;
  body?: unknown;
  setHeader: (name: string, value: string) => void;
  getHeader: (name: string) => string | undefined;
  status: (code: number) => MockResponse;
  json: (body: unknown) => MockResponse;
};

function mockResponse(): MockResponse {
  const headers = new Map<string, unknown>();
  return {
    headers,
    setHeader(name, value) {
      headers.set(name.toLowerCase(), value);
    },
    getHeader(name) {
      return headers.get(name.toLowerCase()) as string | undefined;
    },
    status(code) {
      this.statusCode = code;
      return this;
    },
    json(body) {
      this.body = body;
      return this;
    },
  };
}

function mockRequest(headers: Record<string, string>, remoteAddress = '198.51.100.20') {
  return {
    headers,
    socket: { remoteAddress },
  };
}

describe('FixedWindowRateLimiter', () => {
  it('allows up to the configured limit within a fixed window', () => {
    const limiter = new FixedWindowRateLimiter();
    const policy = { id: 'unit', limit: 2, windowMs: 1000 };

    expect(limiter.check('key', policy, 100).allowed).toBe(true);
    expect(limiter.check('key', policy, 200)).toMatchObject({ allowed: true, remaining: 0 });
    expect(limiter.check('key', policy, 300)).toMatchObject({ allowed: false, remaining: 0, resetAt: 1000 });
  });

  it('resets counts when the fixed window advances', () => {
    const limiter = new FixedWindowRateLimiter();
    const policy = { id: 'unit', limit: 1, windowMs: 1000 };

    expect(limiter.check('key', policy, 999).allowed).toBe(true);
    expect(limiter.check('key', policy, 999).allowed).toBe(false);
    expect(limiter.check('key', policy, 1000)).toMatchObject({ allowed: true, remaining: 0, resetAt: 2000 });
  });
});

describe('applyRateLimit', () => {
  beforeEach(() => {
    _resetRateLimiterForTest();
  });

  it('returns 429 with numeric rate headers and no raw actor details', () => {
    const policy = { id: 'route.test', limit: 1, windowMs: 60 * 1000 };
    const first = mockResponse();
    const second = mockResponse();
    const req = mockRequest({
      'x-forwarded-for': '203.0.113.7, 10.0.0.1',
      'user-agent': 'vitest-agent',
    });

    expect(applyRateLimit(req as never, first as never, policy)).toBe(true);
    expect(first.getHeader('X-RateLimit-Limit')).toBe('1');
    expect(first.getHeader('X-RateLimit-Remaining')).toBe('0');

    expect(applyRateLimit(req as never, second as never, policy)).toBe(false);
    expect(second.statusCode).toBe(429);
    expect(second.body).toEqual({ error: 'rate_limited' });
    expect(second.getHeader('Retry-After')).toMatch(/^\d+$/);
    expect(second.getHeader('X-RateLimit-Reset')).toMatch(/^\d+$/);
    expect(JSON.stringify([...second.headers.entries(), second.body])).not.toContain('203.0.113.7');
    expect(JSON.stringify([...second.headers.entries(), second.body])).not.toContain('vitest-agent');
  });

  it('keys on the first forwarded IP, user-agent, and caller-supplied stable parts', () => {
    const policy = { id: 'route.keyed', limit: 1, windowMs: 60 * 1000 };
    const first = mockRequest({ 'x-forwarded-for': '203.0.113.9, 10.0.0.1', 'user-agent': 'same-ua' });
    const sameFirstIp = mockRequest({ 'x-forwarded-for': '203.0.113.9, 192.0.2.55', 'user-agent': 'same-ua' });
    const differentUser = mockRequest({ 'x-forwarded-for': '203.0.113.9, 10.0.0.1', 'user-agent': 'same-ua' });

    expect(applyRateLimit(first as never, mockResponse() as never, policy, { keyParts: ['user', 'user-1'] })).toBe(true);
    expect(applyRateLimit(sameFirstIp as never, mockResponse() as never, policy, { keyParts: ['user', 'user-1'] })).toBe(false);
    expect(applyRateLimit(differentUser as never, mockResponse() as never, policy, { keyParts: ['user', 'user-2'] })).toBe(true);
  });
});
