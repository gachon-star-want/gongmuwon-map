import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { reporterFingerprint, requireCronSecret } from './http';

type MockResponse = {
  headers: Map<string, unknown>;
  statusCode?: number;
  body?: unknown;
  setHeader: (name: string, value: string) => void;
  getHeader: (name: string) => string | undefined;
  status: (code: number) => MockResponse;
  json: (body: unknown) => MockResponse;
};

const originalCronSecret = process.env.CRON_SECRET;

function mockRequest(headers: Record<string, string>, remoteAddress = '10.0.0.1') {
  return {
    headers,
    socket: { remoteAddress },
  } as never;
}

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

beforeEach(() => {
  delete process.env.CRON_SECRET;
});

afterEach(() => {
  if (originalCronSecret === undefined) {
    delete process.env.CRON_SECRET;
  } else {
    process.env.CRON_SECRET = originalCronSecret;
  }
});

describe('reporterFingerprint', () => {
  it('uses server-observed request data', () => {
    const first = reporterFingerprint(
      mockRequest({
        'x-forwarded-for': '203.0.113.10, 198.51.100.5',
        'user-agent': 'Browser A',
      }),
    );
    const second = reporterFingerprint(
      mockRequest({
        'x-forwarded-for': '203.0.113.10, 198.51.100.99',
        'user-agent': 'Browser A',
      }),
    );

    expect(first).toBe(second);
    expect(first).toHaveLength(64);
  });

  it('changes when the observed browser boundary changes', () => {
    const first = reporterFingerprint(mockRequest({ 'x-forwarded-for': '203.0.113.10', 'user-agent': 'Browser A' }));
    const second = reporterFingerprint(mockRequest({ 'x-forwarded-for': '203.0.113.10', 'user-agent': 'Browser B' }));

    expect(first).not.toBe(second);
  });
});

describe('requireCronSecret', () => {
  it('accepts a matching configured bearer secret', () => {
    process.env.CRON_SECRET = 'cron-secret';
    const res = mockResponse();

    expect(requireCronSecret(mockRequest({ authorization: 'Bearer cron-secret' }), res as never)).toBe(true);
    expect(res.statusCode).toBeUndefined();
    expect(res.body).toBeUndefined();
  });

  it('rejects a wrong configured bearer secret', () => {
    process.env.CRON_SECRET = 'cron-secret';
    const res = mockResponse();

    expect(requireCronSecret(mockRequest({ authorization: 'Bearer wrong-secret' }), res as never)).toBe(false);
    expect(res.statusCode).toBe(401);
    expect(res.body).toEqual({ error: 'unauthorized' });
  });

  it('rejects missing authorization when the secret is configured', () => {
    process.env.CRON_SECRET = 'cron-secret';
    const res = mockResponse();

    expect(requireCronSecret(mockRequest({}), res as never)).toBe(false);
    expect(res.statusCode).toBe(401);
    expect(res.body).toEqual({ error: 'unauthorized' });
  });

  it('fails closed when CRON_SECRET is missing', () => {
    const res = mockResponse();

    expect(requireCronSecret(mockRequest({ authorization: 'Bearer cron-secret' }), res as never)).toBe(false);
    expect(res.statusCode).toBe(503);
    expect(res.body).toEqual({ error: 'cron_secret_not_configured' });
  });

  it('fails closed when CRON_SECRET is blank after trim', () => {
    process.env.CRON_SECRET = '   ';
    const res = mockResponse();

    expect(requireCronSecret(mockRequest({ authorization: 'Bearer cron-secret' }), res as never)).toBe(false);
    expect(res.statusCode).toBe(503);
    expect(res.body).toEqual({ error: 'cron_secret_not_configured' });
  });
});
