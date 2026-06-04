import { writeQuery } from '../_lib/db';
import { parseBody } from '../_lib/http';
import { createSession, normalizeHandle, verifyPassword } from '../_lib/auth';
import { RATE_LIMIT_POLICIES, applyRateLimit } from '../_lib/rate-limit';
import { privateWriteRoute } from '../_lib/route';
import { turnstileTokenFromBody, verifyTurnstileToken } from '../_lib/turnstile';

export default privateWriteRoute(async ({ req, res }) => {
  const body = parseBody(req);
  const handle = String(body.handle || '');
  if (!applyRateLimit(req, res, RATE_LIMIT_POLICIES.authLogin, { keyParts: ['handle', normalizeHandle(handle)] })) {
    return;
  }
  const turnstile = await verifyTurnstileToken(req, turnstileTokenFromBody(body), 'auth_login');
  if (turnstile.ok === false) {
    return { status: turnstile.status, body: { error: turnstile.error } };
  }
  const password = String(body.password || '');
  const { rows } = await writeQuery<{
    id: string;
    handle: string;
    role: string;
    created_at: string;
    password_hash: string;
    password_salt: string;
  }>(
    `
    SELECT id, handle, role, created_at, password_hash, password_salt
    FROM public.app_users
    WHERE handle_normalized = $1
      AND deleted_at IS NULL
    LIMIT 1
  `,
    [normalizeHandle(handle)],
  );
  const user = rows[0];
  if (!user || !(await verifyPassword(password, user.password_salt, user.password_hash))) {
    return { status: 401, body: { error: 'invalid_credentials' } };
  }
  await writeQuery('UPDATE public.app_users SET last_login_at = now() WHERE id = $1', [user.id]);
  await createSession(res, user.id);
  return { status: 200, body: { user: { id: user.id, handle: user.handle, role: user.role, created_at: user.created_at } } };
});
