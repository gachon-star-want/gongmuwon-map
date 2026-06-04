import type { VercelRequest } from '@vercel/node';

export function headerValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export function requestOrigin(req: VercelRequest) {
  const host = headerValue(req.headers['x-forwarded-host']) || headerValue(req.headers.host);
  if (!host) {
    return undefined;
  }
  const proto =
    headerValue(req.headers['x-forwarded-proto']) || (process.env.NODE_ENV === 'production' || process.env.VERCEL ? 'https' : 'http');
  return `${proto.split(',')[0].trim()}://${host}`;
}

export function isJsonContentType(contentType: string | undefined) {
  return contentType?.toLowerCase().split(';')[0]?.trim() === 'application/json';
}

export function isAllowedPrivateOrigin(req: VercelRequest, origin: string | undefined) {
  const allowed = new Set<string>();
  const inferredOrigin = requestOrigin(req);
  if (inferredOrigin) {
    allowed.add(inferredOrigin);
  }
  const publicSiteOrigin = process.env.PUBLIC_SITE_ORIGIN;
  if (publicSiteOrigin) {
    allowed.add(publicSiteOrigin);
  }
  const publicWriteOrigin = process.env.PUBLIC_WRITE_ORIGIN;
  if (publicWriteOrigin) {
    publicWriteOrigin
      .split(',')
      .map((candidate) => candidate.trim())
      .filter(Boolean)
      .forEach((candidate) => allowed.add(candidate));
  }
  if (!origin || allowed.size === 0) {
    return false;
  }
  return allowed.has(origin);
}
