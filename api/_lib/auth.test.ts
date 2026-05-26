import { describe, expect, it } from 'vitest';
import { hashPassword, normalizeHandle, parseCookies, validateHandle, validatePassword, verifyPassword } from './auth';

describe('auth helpers', () => {
  it('normalizes handles for uniqueness', () => {
    expect(normalizeHandle('  맛집 러버_01  ')).toBe('맛집러버_01');
  });

  it('validates handles and passwords', () => {
    expect(validateHandle('공무원맵러버')).toBe(true);
    expect(validateHandle('a')).toBe(false);
    expect(validateHandle('bad handle!')).toBe(false);
    expect(validatePassword('12345678')).toBe(true);
    expect(validatePassword('short')).toBe(false);
  });

  it('hashes and verifies passwords', async () => {
    const result = await hashPassword('correct-password');
    await expect(verifyPassword('correct-password', result.salt, result.hash)).resolves.toBe(true);
    await expect(verifyPassword('wrong-password', result.salt, result.hash)).resolves.toBe(false);
  });

  it('parses cookies', () => {
    expect(parseCookies('a=1; pom_session=hello%20world')).toMatchObject({ a: '1', pom_session: 'hello world' });
  });
});

