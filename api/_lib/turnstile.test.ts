import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { turnstileTokenFromBody, verifyTurnstileToken } from './turnstile';

function mockRequest() {
  return {
    headers: {
      'x-forwarded-for': '203.0.113.10, 10.0.0.1',
    },
    socket: {},
  } as never;
}

describe('turnstile helpers', () => {
  beforeEach(() => {
    delete process.env.TURNSTILE_SECRET_KEY;
    delete process.env.TURNSTILE_SITEVERIFY_URL;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    delete process.env.TURNSTILE_SECRET_KEY;
    delete process.env.TURNSTILE_SITEVERIFY_URL;
  });

  it('reads supported token field names', () => {
    expect(turnstileTokenFromBody({ turnstile_token: ' token-1 ' })).toBe('token-1');
    expect(turnstileTokenFromBody({ turnstileToken: 'token-2' })).toBe('token-2');
    expect(turnstileTokenFromBody({ 'cf-turnstile-response': 'token-3' })).toBe('token-3');
    expect(turnstileTokenFromBody({ turnstile_token: 123 })).toBe('');
  });

  it('fails closed when the server secret is missing', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    await expect(verifyTurnstileToken(mockRequest(), 'token', 'auth_login')).resolves.toEqual({
      ok: false,
      status: 503,
      error: 'turnstile_not_configured',
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('requires a token before calling Siteverify', async () => {
    process.env.TURNSTILE_SECRET_KEY = 'secret';
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    await expect(verifyTurnstileToken(mockRequest(), '', 'auth_login')).resolves.toEqual({
      ok: false,
      status: 400,
      error: 'turnstile_required',
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('verifies the token with Siteverify and sends the caller IP', async () => {
    process.env.TURNSTILE_SECRET_KEY = 'secret';
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ success: true, action: 'auth_login' })));
    vi.stubGlobal('fetch', fetchMock);

    await expect(verifyTurnstileToken(mockRequest(), 'token', 'auth_login')).resolves.toEqual({ ok: true });
    const [, init] = fetchMock.mock.calls[0];
    const body = init?.body as URLSearchParams;
    expect(init?.method).toBe('POST');
    expect(body.get('secret')).toBe('secret');
    expect(body.get('response')).toBe('token');
    expect(body.get('remoteip')).toBe('203.0.113.10');
  });

  it('rejects failed or mismatched actions', async () => {
    process.env.TURNSTILE_SECRET_KEY = 'secret';
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ success: true, action: 'auth_register' }))));

    await expect(verifyTurnstileToken(mockRequest(), 'token', 'auth_login')).resolves.toEqual({
      ok: false,
      status: 403,
      error: 'turnstile_failed',
    });
  });

  it('fails closed when Siteverify is unavailable', async () => {
    process.env.TURNSTILE_SECRET_KEY = 'secret';
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('bad gateway', { status: 502 })));

    await expect(verifyTurnstileToken(mockRequest(), 'token', 'auth_login')).resolves.toEqual({
      ok: false,
      status: 503,
      error: 'turnstile_unavailable',
    });
  });
});
