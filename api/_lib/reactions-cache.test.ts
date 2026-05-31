import { beforeEach, describe, expect, it, vi } from 'vitest';
import { writeQuery } from './db';
import { getCurrentUser } from './auth';
import reactionsHandler from '../v1/places/[id]/reactions';
import { _resetRateLimiterForTest } from './rate-limit';

vi.mock('./db', () => ({
  writeQuery: vi.fn(),
}));

vi.mock('./auth', () => ({
  getCurrentUser: vi.fn(),
}));

type JsonBody = unknown;

type MockResponse = {
  headers: Map<string, unknown>;
  statusCode?: number;
  body?: JsonBody;
  ended: boolean;
  writableEnded: boolean;
  setHeader: (name: string, value: string) => void;
  getHeader: (name: string) => string | undefined;
  status: (code: number) => MockResponse;
  json: (body: JsonBody) => MockResponse;
  end: (body?: string) => void;
};

function mockResponse(): MockResponse {
  const headers = new Map<string, unknown>();
  return {
    headers,
    ended: false,
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
    end(body?: string) {
      this.ended = true;
      this.writableEnded = true;
      if (body !== undefined) {
        this.body = body;
      }
    },
  };
}

const mockedWriteQuery = vi.mocked(writeQuery);
const mockedGetCurrentUser = vi.mocked(getCurrentUser);
const sameOriginHeaders = { origin: 'http://site.example.com', host: 'site.example.com' };

describe('reactions route cache policy', () => {
  beforeEach(() => {
    _resetRateLimiterForTest();
    mockedWriteQuery.mockReset();
    mockedGetCurrentUser.mockReset();
  });

  it('sets private no-store for GET summaries', async () => {
    mockedGetCurrentUser.mockResolvedValue({ id: 'user-1' } as never);
    mockedWriteQuery
      .mockResolvedValueOnce({ rows: [{ like_count: 7, dislike_count: 2 }] } as never)
      .mockResolvedValueOnce({ rows: [{ reaction: 'like' }] } as never);

    const res = mockResponse();
    await reactionsHandler({ method: 'GET', query: { id: 'place-1' }, headers: {} } as never, res as never);

    expect(res.statusCode).toBe(200);
    expect(res.getHeader('Cache-Control')).toBe('private, no-store');
    expect(res.getHeader('Access-Control-Allow-Origin')).toBe('*');
    expect(res.body).toEqual({ like_count: 7, dislike_count: 2, user_reaction: 'like' });
  });

  it('sets private no-store for POST mutation responses', async () => {
    mockedGetCurrentUser.mockResolvedValue({ id: 'user-1' } as never);
    mockedWriteQuery
      .mockResolvedValueOnce({ rows: [] } as never)
      .mockResolvedValueOnce({ rows: [{ like_count: 8, dislike_count: 2 }] } as never)
      .mockResolvedValueOnce({ rows: [{ reaction: 'dislike' }] } as never);

    const res = mockResponse();
    await reactionsHandler(
      { method: 'POST', query: { id: 'place-1' }, headers: sameOriginHeaders, body: { reaction: 'dislike' } } as never,
      res as never,
    );

    expect(res.statusCode).toBe(200);
    expect(res.getHeader('Cache-Control')).toBe('private, no-store');
    expect(res.getHeader('Access-Control-Allow-Origin')).toBe('http://site.example.com');
    expect(res.body).toEqual({ like_count: 8, dislike_count: 2, user_reaction: 'dislike' });
  });

  it('sets private no-store for unauthenticated POST errors', async () => {
    mockedGetCurrentUser.mockResolvedValue(null);

    const res = mockResponse();
    await reactionsHandler(
      { method: 'POST', query: { id: 'place-1' }, headers: sameOriginHeaders, body: { reaction: 'like' } } as never,
      res as never,
    );

    expect(res.statusCode).toBe(401);
    expect(res.getHeader('Cache-Control')).toBe('private, no-store');
    expect(res.getHeader('Access-Control-Allow-Origin')).toBe('http://site.example.com');
    expect(res.body).toEqual({ error: 'login_required' });
  });

  it('keeps OPTIONS support and no-store policy', async () => {
    const res = mockResponse();
    await reactionsHandler({ method: 'OPTIONS', query: { id: 'place-1' }, headers: {} } as never, res as never);

    expect(res.statusCode).toBe(204);
    expect(res.getHeader('Cache-Control')).toBe('private, no-store');
    expect(res.getHeader('Access-Control-Allow-Origin')).toBe('*');
    expect(res.getHeader('Access-Control-Allow-Methods')).toContain('GET');
    expect(res.getHeader('Access-Control-Allow-Methods')).toContain('POST');
  });

  it('echoes allowed origin for POST preflight without wildcard CORS', async () => {
    const res = mockResponse();
    await reactionsHandler(
      {
        method: 'OPTIONS',
        query: { id: 'place-1' },
        headers: { ...sameOriginHeaders, 'access-control-request-method': 'POST' },
      } as never,
      res as never,
    );

    expect(res.statusCode).toBe(204);
    expect(res.getHeader('Cache-Control')).toBe('private, no-store');
    expect(res.getHeader('Access-Control-Allow-Origin')).toBe('http://site.example.com');
    expect(res.getHeader('Vary')).toBe('Origin');
  });

  it('rejects unapproved origins for POST preflight and mutation', async () => {
    const preflight = mockResponse();
    await reactionsHandler(
      {
        method: 'OPTIONS',
        query: { id: 'place-1' },
        headers: {
          origin: 'https://evil.example',
          host: 'site.example.com',
          'access-control-request-method': 'POST',
        },
      } as never,
      preflight as never,
    );

    expect(preflight.statusCode).toBe(403);
    expect(preflight.getHeader('Cache-Control')).toBe('private, no-store');
    expect(preflight.getHeader('Access-Control-Allow-Origin')).toBeUndefined();

    const post = mockResponse();
    await reactionsHandler(
      {
        method: 'POST',
        query: { id: 'place-1' },
        headers: { origin: 'https://evil.example', host: 'site.example.com' },
        body: { reaction: 'like' },
      } as never,
      post as never,
    );

    expect(post.statusCode).toBe(403);
    expect(post.getHeader('Cache-Control')).toBe('private, no-store');
    expect(post.getHeader('Access-Control-Allow-Origin')).toBeUndefined();
    expect(mockedGetCurrentUser).not.toHaveBeenCalled();
  });

  it('returns 405 for invalid methods with no-store', async () => {
    mockedGetCurrentUser.mockResolvedValue(null);
    const res = mockResponse();
    await reactionsHandler({ method: 'DELETE', query: { id: 'place-1' }, headers: {} } as never, res as never);

    expect(res.statusCode).toBe(405);
    expect(res.getHeader('Allow')).toBe('GET, HEAD, POST, OPTIONS');
    expect(res.getHeader('Cache-Control')).toBe('private, no-store');
    expect(res.body).toEqual({ error: 'method_not_allowed' });
  });

  it('rate-limits POST reactions without applying the limit to GET', async () => {
    mockedGetCurrentUser.mockResolvedValue({ id: 'user-1' } as never);
    const req = {
      method: 'POST',
      query: { id: 'place-1' },
      headers: {
        ...sameOriginHeaders,
        'x-forwarded-for': '203.0.113.44, 10.0.0.1',
        'user-agent': 'vitest-agent',
      },
      body: { reaction: 'invalid' },
    };

    for (let index = 0; index < 60; index += 1) {
      const res = mockResponse();
      await reactionsHandler(req as never, res as never);
      expect(res.statusCode).toBe(400);
      expect(res.body).toEqual({ error: 'invalid_reaction' });
    }

    const limited = mockResponse();
    await reactionsHandler(req as never, limited as never);

    expect(limited.statusCode).toBe(429);
    expect(limited.getHeader('Cache-Control')).toBe('private, no-store');
    expect(limited.getHeader('Retry-After')).toMatch(/^\d+$/);
    expect(limited.getHeader('X-RateLimit-Limit')).toBe('60');
    expect(limited.getHeader('X-RateLimit-Remaining')).toBe('0');
    expect(limited.body).toEqual({ error: 'rate_limited' });
    expect(mockedWriteQuery).not.toHaveBeenCalled();

    mockedWriteQuery
      .mockResolvedValueOnce({ rows: [{ like_count: 1, dislike_count: 0 }] } as never)
      .mockResolvedValueOnce({ rows: [] } as never);
    const getRes = mockResponse();
    await reactionsHandler(
      {
        method: 'GET',
        query: { id: 'place-1' },
        headers: { 'x-forwarded-for': '203.0.113.44, 10.0.0.1', 'user-agent': 'vitest-agent' },
      } as never,
      getRes as never,
    );

    expect(getRes.statusCode).toBe(200);
    expect(getRes.getHeader('Cache-Control')).toBe('private, no-store');
    expect(getRes.body).toEqual({ like_count: 1, dislike_count: 0, user_reaction: null });
  });
});
