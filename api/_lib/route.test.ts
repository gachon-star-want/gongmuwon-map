import { beforeEach, describe, expect, it } from 'vitest';
import { privateWriteRoute, publicReadRoute } from './route';

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

const trustedWriteHeaders = {
  origin: 'https://site.example.com',
  host: 'site.example.com',
  'x-forwarded-proto': 'https',
  'content-type': 'application/json',
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

describe('publicReadRoute', () => {
  it('accepts GET', async () => {
    const res = mockResponse();
    const handler = publicReadRoute(async () => ({ hello: 'world' }));
    await handler({ method: 'GET', query: {}, headers: {} } as never, res);

    expect(res.statusCode).toBe(200);
    expect(res.getHeader('Access-Control-Allow-Origin')).toBe('*');
    expect(res.body).toEqual({ hello: 'world' });
  });

  it('accepts HEAD', async () => {
    const res = mockResponse();
    const handler = publicReadRoute(async () => ({ hello: 'world' }));
    await handler({ method: 'HEAD', query: {}, headers: {} } as never, res);

    expect(res.statusCode).toBe(200);
  });

  it('accepts OPTIONS', async () => {
    const res = mockResponse();
    const handler = publicReadRoute(async () => ({ hello: 'world' }));
    await handler({ method: 'OPTIONS', query: {}, headers: {} } as never, res);

    expect(res.statusCode).toBe(204);
    expect(res.getHeader('Access-Control-Allow-Origin')).toBe('*');
    expect(res.getHeader('Access-Control-Allow-Methods')).toContain('GET');
  });

  it('rejects POST with 405', async () => {
    const res = mockResponse();
    const handler = publicReadRoute(async () => ({ hello: 'world' }));
    await handler({ method: 'POST', query: {}, headers: {} } as never, res);

    expect(res.statusCode).toBe(405);
    expect(res.body).toEqual({ error: 'method_not_allowed' });
  });

  it('applies cache control for successful reads', async () => {
    const res = mockResponse();
    const handler = publicReadRoute(async () => ({ hello: 'world' }), { cache: true });
    await handler({ method: 'GET', query: {}, headers: {} } as never, res);

    expect(res.getHeader('Cache-Control')).toBe('public, s-maxage=300, stale-while-revalidate=600');
  });

  it('does not set cache on explicit read errors', async () => {
    const res = mockResponse();
    const handler = publicReadRoute(async () => ({ status: 400, body: { error: 'bad' } }), { cache: true });
    await handler({ method: 'GET', query: {}, headers: {} } as never, res);

    expect(res.statusCode).toBe(400);
    expect(res.getHeader('Cache-Control')).toBeUndefined();
  });
});

describe('privateWriteRoute', () => {
  beforeEach(() => {
    delete process.env.PUBLIC_SITE_ORIGIN;
    delete process.env.PUBLIC_WRITE_ORIGIN;
  });

  it('accepts POST', async () => {
    const res = mockResponse();
    const handler = privateWriteRoute(async () => ({ status: 200, body: { ok: true } }));
    await handler({ method: 'POST', query: {}, headers: trustedWriteHeaders } as never, res);

    expect(res.statusCode).toBe(200);
    expect(res.body).toEqual({ ok: true });
  });

  it('accepts OPTIONS', async () => {
    const res = mockResponse();
    const handler = privateWriteRoute(async () => ({ ok: true }));
    await handler({ method: 'OPTIONS', query: {}, headers: trustedWriteHeaders } as never, res);

    expect(res.statusCode).toBe(204);
  });

  it('rejects GET with 405', async () => {
    const res = mockResponse();
    const handler = privateWriteRoute(async () => ({ ok: true }));
    await handler({ method: 'GET', query: {}, headers: trustedWriteHeaders } as never, res);

    expect(res.statusCode).toBe(405);
    expect(res.body).toEqual({ error: 'method_not_allowed' });
  });

  it('rejects missing Origin', async () => {
    const res = mockResponse();
    const handler = privateWriteRoute(async () => ({ ok: true }));
    await handler({ method: 'POST', query: {}, headers: { host: 'site.example.com', 'content-type': 'application/json' } } as never, res);

    expect(res.statusCode).toBe(403);
    expect(res.body).toEqual({ error: 'forbidden' });
  });

  it('rejects non-json POST bodies', async () => {
    const res = mockResponse();
    const handler = privateWriteRoute(async () => ({ ok: true }));
    await handler({
      method: 'POST',
      query: {},
      headers: { ...trustedWriteHeaders, 'content-type': 'text/plain' },
    } as never, res);

    expect(res.statusCode).toBe(415);
    expect(res.body).toEqual({ error: 'unsupported_media_type' });
  });

  it('accepts PUBLIC_SITE_ORIGIN', async () => {
    process.env.PUBLIC_SITE_ORIGIN = 'https://site.example.com';
    const res = mockResponse();
    const handler = privateWriteRoute(async () => ({ ok: true }));
    await handler({ method: 'POST', query: {}, headers: trustedWriteHeaders } as never, res);

    expect(res.statusCode).toBe(200);
    expect(res.getHeader('Access-Control-Allow-Origin')).toBe('https://site.example.com');
  });

  it('accepts comma-separated PUBLIC_WRITE_ORIGIN', async () => {
    process.env.PUBLIC_WRITE_ORIGIN = 'https://a.example.com, https://b.example.com';
    const res = mockResponse();
    const handler = privateWriteRoute(async () => ({ ok: true }));
    await handler({
      method: 'POST',
      query: {},
      headers: { ...trustedWriteHeaders, origin: 'https://b.example.com' },
    } as never, res);

    expect(res.statusCode).toBe(200);
    expect(res.getHeader('Access-Control-Allow-Origin')).toBe('https://b.example.com');
  });

  it('rejects unapproved Origin', async () => {
    process.env.PUBLIC_WRITE_ORIGIN = 'https://approved.example.com';
    const res = mockResponse();
    const handler = privateWriteRoute(async () => ({ ok: true }));
    await handler({
      method: 'POST',
      query: {},
      headers: { ...trustedWriteHeaders, origin: 'https://evil.example.com' },
    } as never, res);

    expect(res.statusCode).toBe(403);
    expect(res.body).toEqual({ error: 'forbidden' });
  });

  it('does not set cache for write routes', async () => {
    const res = mockResponse();
    const handler = privateWriteRoute(async () => ({ ok: true }));
    await handler({ method: 'POST', query: {}, headers: trustedWriteHeaders } as never, res);

    expect(res.getHeader('Cache-Control')).toBeUndefined();
  });
});
