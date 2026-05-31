import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

type HeaderEntry = {
  key?: unknown;
  value?: unknown;
};

type HeaderRule = {
  source?: unknown;
  headers?: HeaderEntry[];
};

type VercelConfig = {
  headers?: HeaderRule[];
};

function loadVercelConfig(): VercelConfig {
  const file = path.resolve(process.cwd(), 'vercel.json');
  const raw = fs.readFileSync(file, 'utf8');
  return JSON.parse(raw) as VercelConfig;
}

describe('vercel /api/v1 headers', () => {
  it('does not apply broad Cache-Control headers and keeps CORS', () => {
    const config = loadVercelConfig();
    const headerRules = Array.isArray(config.headers) ? config.headers : [];
    const apiV1Rules = headerRules.filter((rule) => typeof rule.source === 'string' && rule.source.startsWith('/api/v1'));

    expect(apiV1Rules.length).toBeGreaterThan(0);

    const hasApiV1CacheControl = apiV1Rules.some((rule) =>
      (Array.isArray(rule.headers) ? rule.headers : []).some(
        (entry) => typeof entry.key === 'string' && entry.key.toLowerCase() === 'cache-control',
      ),
    );
    expect(hasApiV1CacheControl).toBe(false);

    const broadRule = apiV1Rules.find((rule) => rule.source === '/api/v1/(.*)');
    expect(broadRule).toBeTruthy();
    const hasCorsAllowAll = (Array.isArray(broadRule?.headers) ? broadRule.headers : []).some(
      (entry) =>
        typeof entry.key === 'string' &&
        entry.key.toLowerCase() === 'access-control-allow-origin' &&
        entry.value === '*',
    );
    expect(hasCorsAllowAll).toBe(true);
  });
});
