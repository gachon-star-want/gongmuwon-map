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
  function canApplyToApiV1(source: unknown) {
    if (typeof source !== 'string') {
      return false;
    }
    if (source === '/(.*)' || source === '/*' || source === '/:path*') {
      return true;
    }
    if (source === '/api/(.*)' || source === '/api/*' || source === '/api/:path*') {
      return true;
    }
    return /^\/api\/v1(?:$|[/:*(])/.test(source);
  }

  it('does not configure API v1 CORS or cache headers in vercel.json', () => {
    const config = loadVercelConfig();
    const headerRules = Array.isArray(config.headers) ? config.headers : [];
    const apiV1Rules = headerRules.filter((rule) => canApplyToApiV1(rule.source));

    const forbiddenHeaders = apiV1Rules.flatMap((rule) =>
      (Array.isArray(rule.headers) ? rule.headers : [])
        .filter(
          (entry) =>
            typeof entry.key === 'string' &&
            ['access-control-allow-origin', 'cache-control'].includes(entry.key.toLowerCase()),
        )
        .map((entry) => ({ source: rule.source, key: entry.key, value: entry.value })),
    );

    expect(forbiddenHeaders).toEqual([]);
  });
});
