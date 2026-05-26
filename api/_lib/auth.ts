import type { VercelRequest, VercelResponse } from '@vercel/node';
import crypto from 'node:crypto';
import { promisify } from 'node:util';
import { writeQuery } from './db';

const scrypt = promisify(crypto.scrypt);
const SESSION_COOKIE = 'pom_session';
const SESSION_TTL_SECONDS = 60 * 60 * 24 * 30;

export type AuthUser = {
  id: string;
  handle: string;
  role: string;
  created_at: string;
};

export function normalizeHandle(handle: string) {
  return handle.trim().replace(/\s+/g, '').toLowerCase();
}

export function validateHandle(handle: string) {
  const trimmed = handle.trim();
  if (trimmed.length < 2 || trimmed.length > 24) return false;
  return /^[\p{L}\p{N}_-]+$/u.test(trimmed);
}

export function validatePassword(password: string) {
  return password.length >= 8 && password.length <= 128;
}

export async function hashPassword(password: string) {
  const salt = crypto.randomBytes(16).toString('base64url');
  const derived = (await scrypt(password, salt, 64)) as Buffer;
  return { salt, hash: derived.toString('hex') };
}

export async function verifyPassword(password: string, salt: string, expectedHash: string) {
  const derived = (await scrypt(password, salt, 64)) as Buffer;
  const actual = Buffer.from(derived.toString('hex'), 'hex');
  const expected = Buffer.from(expectedHash, 'hex');
  if (actual.length !== expected.length) return false;
  return crypto.timingSafeEqual(actual, expected);
}

export function tokenHash(token: string) {
  return crypto.createHash('sha256').update(token).digest('hex');
}

export function parseCookies(header: string | string[] | undefined) {
  const source = Array.isArray(header) ? header.join(';') : header || '';
  return Object.fromEntries(
    source
      .split(';')
      .map((part) => part.trim())
      .filter(Boolean)
      .map((part) => {
        const index = part.indexOf('=');
        if (index === -1) return [part, ''];
        return [part.slice(0, index), decodeURIComponent(part.slice(index + 1))];
      }),
  );
}

function cookieBase() {
  const secure = process.env.NODE_ENV === 'production' || Boolean(process.env.VERCEL);
  return `HttpOnly; SameSite=Lax; Path=/; ${secure ? 'Secure; ' : ''}`;
}

export function setSessionCookie(res: VercelResponse, token: string) {
  res.setHeader('Set-Cookie', `${SESSION_COOKIE}=${encodeURIComponent(token)}; ${cookieBase()}Max-Age=${SESSION_TTL_SECONDS}`);
}

export function clearSessionCookie(res: VercelResponse) {
  res.setHeader('Set-Cookie', `${SESSION_COOKIE}=; ${cookieBase()}Max-Age=0`);
}

export function sessionTokenFromRequest(req: VercelRequest) {
  return parseCookies(req.headers.cookie)[SESSION_COOKIE];
}

export async function createSession(res: VercelResponse, userId: string) {
  const token = crypto.randomBytes(32).toString('base64url');
  const hash = tokenHash(token);
  await writeQuery(
    `
    INSERT INTO public.app_sessions (user_id, token_hash, expires_at)
    VALUES ($1, $2, now() + interval '30 days')
  `,
    [userId, hash],
  );
  setSessionCookie(res, token);
}

export async function getCurrentUser(req: VercelRequest): Promise<AuthUser | null> {
  const token = sessionTokenFromRequest(req);
  if (!token) return null;
  const hash = tokenHash(token);
  const { rows } = await writeQuery<AuthUser>(
    `
    SELECT u.id, u.handle, u.role, u.created_at
    FROM public.app_sessions s
    JOIN public.app_users u ON u.id = s.user_id
    WHERE s.token_hash = $1
      AND s.expires_at > now()
      AND u.deleted_at IS NULL
    LIMIT 1
  `,
    [hash],
  );
  if (!rows[0]) return null;
  await writeQuery('UPDATE public.app_sessions SET last_seen_at = now() WHERE token_hash = $1', [hash]);
  return rows[0];
}

export async function destroySession(req: VercelRequest, res: VercelResponse) {
  const token = sessionTokenFromRequest(req);
  if (token) {
    await writeQuery('DELETE FROM public.app_sessions WHERE token_hash = $1', [tokenHash(token)]);
  }
  clearSessionCookie(res);
}

