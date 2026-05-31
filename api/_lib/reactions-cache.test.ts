import { beforeEach, describe, expect, it, vi } from 'vitest';
import { writeQuery } from './db';
import { getCurrentUser } from './auth';
import reactionsHandler from '../v1/places/[id]/reactions';

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

describe('reactions route cache policy', () => {
  beforeEach(() => {
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
      { method: 'POST', query: { id: 'place-1' }, headers: {}, body: { reaction: 'dislike' } } as never,
      res as never,
    );

    expect(res.statusCode).toBe(200);
    expect(res.getHeader('Cache-Control')).toBe('private, no-store');
    expect(res.body).toEqual({ like_count: 8, dislike_count: 2, user_reaction: 'dislike' });
  });

  it('sets private no-store for unauthenticated POST errors', async () => {
    mockedGetCurrentUser.mockResolvedValue(null);

    const res = mockResponse();
    await reactionsHandler(
      { method: 'POST', query: { id: 'place-1' }, headers: {}, body: { reaction: 'like' } } as never,
      res as never,
    );

    expect(res.statusCode).toBe(401);
    expect(res.getHeader('Cache-Control')).toBe('private, no-store');
    expect(res.body).toEqual({ error: 'login_required' });
  });

  it('keeps OPTIONS support and no-store policy', async () => {
    const res = mockResponse();
    await reactionsHandler({ method: 'OPTIONS', query: { id: 'place-1' }, headers: {} } as never, res as never);

    expect(res.statusCode).toBe(204);
    expect(res.getHeader('Cache-Control')).toBe('private, no-store');
    expect(res.getHeader('Access-Control-Allow-Methods')).toContain('GET');
    expect(res.getHeader('Access-Control-Allow-Methods')).toContain('POST');
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
});
