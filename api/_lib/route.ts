import type { VercelRequest, VercelResponse } from '@vercel/node';
import { sendJson } from './http';

type JsonPayload = { status?: number; body: unknown };

export type RouteContext = {
  req: VercelRequest;
  res: VercelResponse;
};

export type PublicReadOptions = {
  cache?: boolean | string;
};

function headerValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function requestOrigin(req: VercelRequest) {
  const host = headerValue(req.headers['x-forwarded-host']) || headerValue(req.headers.host);
  if (!host) {
    return undefined;
  }
  const proto =
    headerValue(req.headers['x-forwarded-proto']) || (process.env.NODE_ENV === 'production' || process.env.VERCEL ? 'https' : 'http');
  return `${proto.split(',')[0].trim()}://${host}`;
}

function isJsonContentType(contentType: string | undefined) {
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

function parseRouteResponse(result: unknown): [number, unknown] {
  if (
    result !== null &&
    typeof result === 'object' &&
    'status' in result &&
    'body' in (result as { status?: unknown; body?: unknown })
  ) {
    const status = (result as { status?: unknown }).status;
    if (typeof status === 'number') {
      return [status, (result as JsonPayload).body];
    }
  }
  return [200, result];
}

function sendPrivateJson(res: VercelResponse, status: number, body: unknown) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.status(status).json(body);
}

export function publicReadRoute(handler: (ctx: RouteContext) => Promise<unknown>, options?: PublicReadOptions) {
  const cache = options?.cache;
  return async (req: VercelRequest, res: VercelResponse) => {
    const requestMethod = req.method === 'HEAD' ? 'GET' : req.method;
    if (!req.method) {
      sendJson(res, 400, { error: 'invalid_request' }, false, true);
      return;
    }

    if (requestMethod === 'OPTIONS') {
      res.setHeader('Access-Control-Allow-Origin', '*');
      res.setHeader('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      res.status(204).end();
      return;
    }

    if (requestMethod !== 'GET') {
      res.setHeader('Allow', 'GET, HEAD, OPTIONS');
      sendJson(res, 405, { error: 'method_not_allowed' }, false, true);
      return;
    }

    try {
      const result = await handler({ req, res });
      if (res.writableEnded) {
        return;
      }
      const [status, body] = parseRouteResponse(result);
      sendJson(res, status, body, status < 400 ? cache : false, true);
    } catch {
      sendJson(res, 500, { error: 'internal_error' }, false, true);
    }
  };
}

export function privateWriteRoute(handler: (ctx: RouteContext) => Promise<unknown>) {
  return async (req: VercelRequest, res: VercelResponse) => {
    const requestMethod = req.method === 'HEAD' ? 'GET' : req.method;
    if (!req.method) {
      sendPrivateJson(res, 400, { error: 'invalid_request' });
      return;
    }

    const originHeader = req.headers.origin;
    const origin = Array.isArray(originHeader) ? originHeader[0] : originHeader;
    if (!isAllowedPrivateOrigin(req, typeof origin === 'string' ? origin : undefined)) {
      res.setHeader('Vary', 'Origin');
      sendPrivateJson(res, 403, { error: 'forbidden' });
      return;
    }
    if (origin) {
      res.setHeader('Access-Control-Allow-Origin', origin);
    }
    res.setHeader('Vary', 'Origin');

    if (requestMethod === 'OPTIONS') {
      res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      res.status(204).end();
      return;
    }
    if (requestMethod !== 'POST') {
      res.setHeader('Allow', 'POST, OPTIONS');
      sendPrivateJson(res, 405, { error: 'method_not_allowed' });
      return;
    }
    if (!isJsonContentType(headerValue(req.headers['content-type']))) {
      sendPrivateJson(res, 415, { error: 'unsupported_media_type' });
      return;
    }

    try {
      const result = await handler({ req, res });
      if (res.writableEnded) {
        return;
      }
      const [status, body] = parseRouteResponse(result);
      sendPrivateJson(res, status, body);
    } catch {
      sendPrivateJson(res, 500, { error: 'internal_error' });
    }
  };
}
