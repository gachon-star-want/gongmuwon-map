import { writeQuery } from '../_lib/db';
import { parseBody } from '../_lib/http';
import { createSession, hashPassword, normalizeHandle, validateHandle, validatePassword } from '../_lib/auth';
import { RATE_LIMIT_POLICIES, applyRateLimit } from '../_lib/rate-limit';
import { privateWriteRoute } from '../_lib/route';
import { turnstileTokenFromBody, verifyTurnstileToken } from '../_lib/turnstile';

export default privateWriteRoute(async ({ req, res }) => {
  if (!applyRateLimit(req, res, RATE_LIMIT_POLICIES.authRegister)) {
    return;
  }
  const body = parseBody(req);
  const turnstile = await verifyTurnstileToken(req, turnstileTokenFromBody(body), 'auth_register');
  if (turnstile.ok === false) {
    return { status: turnstile.status, body: { error: turnstile.error } };
  }
  const handle = String(body.handle || '').trim();
  const password = String(body.password || '');
  if (!validateHandle(handle)) {
    return { status: 400, body: { error: 'invalid_handle' } };
  }
  if (!validatePassword(password)) {
    return { status: 400, body: { error: 'invalid_password' } };
  }

  try {
    const passwordResult = await hashPassword(password);
    const { rows } = await writeQuery<{ id: string; handle: string; role: string; created_at: string }>(
      `
      INSERT INTO public.app_users (handle, handle_normalized, password_hash, password_salt)
      VALUES ($1, $2, $3, $4)
      RETURNING id, handle, role, created_at
    `,
      [handle, normalizeHandle(handle), passwordResult.hash, passwordResult.salt],
    );
    await createSession(res, rows[0].id);
    return { status: 201, body: { user: rows[0] } };
  } catch (error) {
    console.error('register:', error);
    if ((error as { code?: string }).code === '23505') {
      return { status: 409, body: { error: 'handle_taken' } };
    }
    throw error;
  }
});
