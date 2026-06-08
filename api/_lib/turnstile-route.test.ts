import { beforeEach, describe, expect, it, vi } from 'vitest';
import { writeQuery } from './db';
import { _resetRateLimiterForTest } from './rate-limit';
import loginHandler from '../auth/login';
import logoutHandler from '../auth/logout';
import registerHandler from '../auth/register';
import communityPostsHandler from '../community/posts';
import communityCommentsHandler from '../community/posts/[id]/comments';
import closureReportHandler from '../closure-report';
import takedownRequestHandler from '../takedown-request';

vi.mock('./db', () => ({
  writeQuery: vi.fn(),
}));

vi.mock('./turnstile', () => ({
  turnstileTokenFromBody: (body: any) => body?.turnstile_token ?? '',
  verifyTurnstileToken: vi.fn(async (req, token, expectedAction) => {
    if (!token) {
      return { ok: false, status: 400, error: 'turnstile_required' };
    }
    if (token === 'invalid-token') {
      return { ok: false, status: 403, error: 'turnstile_failed' };
    }
    return { ok: true };
  }),
}));

type MockResponse = {
  headers: Map<string, unknown>;
  statusCode?: number;
  body?: unknown;
  writableEnded: boolean;
  setHeader: (name: string, value: string) => void;
  getHeader: (name: string) => string | undefined;
  status: (code: number) => MockResponse;
  json: (body: unknown) => MockResponse;
  end: () => void;
};

function mockResponse(): MockResponse {
  const headers = new Map<string, unknown>();
  return {
    headers,
    writableEnded: false,
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
    end() {
      this.writableEnded = true;
    },
  };
}

const trustedWriteHeaders = {
  origin: 'https://site.example.com',
  host: 'site.example.com',
  'x-forwarded-proto': 'https',
  'content-type': 'application/json',
  'user-agent': 'vitest-agent',
  'x-forwarded-for': '203.0.113.25',
};

const untrustedWriteHeaders = {
  ...trustedWriteHeaders,
  origin: 'https://evil.example.com',
};

describe('turnstile-protected write routes', () => {
  const mockedWriteQuery = vi.mocked(writeQuery);

  beforeEach(() => {
    _resetRateLimiterForTest();
    mockedWriteQuery.mockReset();
    process.env.TURNSTILE_SECRET_KEY = 'secret';
  });

  it('rejects takedown requests without a Turnstile token before DB writes', async () => {
    const res = mockResponse();
    await takedownRequestHandler(
      {
        method: 'POST',
        query: {},
        headers: trustedWriteHeaders,
        body: {
          place_id: '11111111-1111-1111-1111-111111111111',
          reason: '식당 정보 오류: '.padEnd(60, '가'),
          email: 'owner@example.com',
        },
      } as never,
      res as never,
    );

    expect(res.statusCode).toBe(400);
    expect(res.body).toEqual({ error: 'turnstile_required' });
    expect(mockedWriteQuery).not.toHaveBeenCalled();
  });

  it('rejects closure reports without a Turnstile token before DB writes', async () => {
    const res = mockResponse();
    await closureReportHandler(
      {
        method: 'POST',
        query: {},
        headers: trustedWriteHeaders,
        body: {
          place_id: '11111111-1111-1111-1111-111111111111',
          note: 'web-ui-report',
        },
      } as never,
      res as never,
    );

    expect(res.statusCode).toBe(400);
    expect(res.body).toEqual({ error: 'turnstile_required' });
    expect(mockedWriteQuery).not.toHaveBeenCalled();
  });

  it('rejects logins without a Turnstile token before DB writes', async () => {
    const res = mockResponse();
    await loginHandler(
      {
        method: 'POST',
        query: {},
        headers: trustedWriteHeaders,
        body: {
          handle: 'tester',
          password: 'password123',
        },
      } as never,
      res as never,
    );

    expect(res.statusCode).toBe(400);
    expect(res.body).toEqual({ error: 'turnstile_required' });
    expect(mockedWriteQuery).not.toHaveBeenCalled();
  });

  it('rejects registrations without a Turnstile token before DB writes', async () => {
    const res = mockResponse();
    await registerHandler(
      {
        method: 'POST',
        query: {},
        headers: trustedWriteHeaders,
        body: {
          handle: 'tester',
          password: 'password123',
        },
      } as never,
      res as never,
    );

    expect(res.statusCode).toBe(400);
    expect(res.body).toEqual({ error: 'turnstile_required' });
    expect(mockedWriteQuery).not.toHaveBeenCalled();
  });

  it.each([
    [
      'login',
      loginHandler,
      { query: {}, body: { handle: 'tester', password: 'password123', turnstile_token: 'token' } },
    ],
    [
      'register',
      registerHandler,
      { query: {}, body: { handle: 'tester', password: 'password123', turnstile_token: 'token' } },
    ],
    [
      'community post',
      communityPostsHandler,
      { query: {}, body: { title: 'hello', body: 'world', category: 'free', turnstile_token: 'token' } },
    ],
    [
      'community comment',
      communityCommentsHandler,
      { query: { id: '11111111-1111-1111-1111-111111111111' }, body: { body: 'hello', turnstile_token: 'token' } },
    ],
  ])('rejects untrusted Origin for %s before DB writes', async (_label, handler, request) => {
    const res = mockResponse();
    await handler(
      {
        method: 'POST',
        headers: untrustedWriteHeaders,
        ...request,
      } as never,
      res as never,
    );

    expect(res.statusCode).toBe(403);
    expect(res.body).toEqual({ error: 'forbidden' });
    expect(mockedWriteQuery).not.toHaveBeenCalled();
  });

  it('rejects logout from an untrusted Origin before deleting the session', async () => {
    const res = mockResponse();
    await logoutHandler(
      {
        method: 'POST',
        query: {},
        headers: untrustedWriteHeaders,
        body: {},
      } as never,
      res as never,
    );

    expect(res.statusCode).toBe(403);
    expect(res.body).toEqual({ error: 'forbidden' });
    expect(mockedWriteQuery).not.toHaveBeenCalled();
  });

  it('rejects takedown requests with invalid fields even with Turnstile token', async () => {
    const res = mockResponse();
    await takedownRequestHandler(
      {
        method: 'POST',
        query: {},
        headers: trustedWriteHeaders,
        body: {
          place_id: '11111111-1111-1111-1111-111111111111',
          reason: '너무 짧음',
          email: 'invalid-email',
          turnstile_token: 'valid-token',
        },
      } as never,
      res as never,
    );

    expect(res.statusCode).toBe(400);
    expect(res.body).toEqual({ error: 'invalid_request' });
    expect(mockedWriteQuery).not.toHaveBeenCalled();
  });

  it('accepts takedown requests with valid fields and writes to DB', async () => {
    const res = mockResponse();
    mockedWriteQuery.mockResolvedValueOnce({ rows: [{ result: { ok: true, request_id: 'req-123', place_id: '11111111-1111-1111-1111-111111111111', hidden: true } }] } as any);
    await takedownRequestHandler(
      {
        method: 'POST',
        query: {},
        headers: trustedWriteHeaders,
        body: {
          place_id: '11111111-1111-1111-1111-111111111111',
          reason: '식당 정보 오류: '.padEnd(60, '가'),
          email: 'owner@example.com',
          turnstile_token: 'valid-token',
        },
      } as never,
      res as never,
    );

    expect(res.body).toEqual({ ok: true, request_id: 'req-123', place_id: '11111111-1111-1111-1111-111111111111', hidden: true });
    expect(mockedWriteQuery).toHaveBeenCalledWith(
      'SELECT public.request_takedown($1::uuid, $2::text, $3::text) AS result',
      [
        '11111111-1111-1111-1111-111111111111',
        '식당 정보 오류: '.padEnd(60, '가'),
        'owner@example.com',
      ],
    );
  });
});
