import type { VercelRequest, VercelResponse } from '@vercel/node';
import { query } from './_lib/db';
import { methodGuard } from './_lib/http';

const BASE_URL = 'https://xn--ob0bo0wl1ax52a.com';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (!methodGuard(req, res, ['GET'])) return;

  const { rows } = await query<{ id: string; name: string; last_visit_at: string | null }>(
    `
    SELECT id::text, name, last_visit_at::text
    FROM public.places_public
    ORDER BY score DESC NULLS LAST
    LIMIT 5000
    `,
  );

  const staticUrls = ['', '/about', '/privacy', '/terms', '/disclaimer', '/legal', '/api'];
  const urls = [
    ...staticUrls.map((path) => xmlUrl(`${BASE_URL}${path}`, null)),
    ...rows.map((row) => xmlUrl(`${BASE_URL}/r/${slug(row.name)}-${row.id}`, row.last_visit_at)),
  ];

  res.setHeader('Content-Type', 'application/xml; charset=utf-8');
  res.setHeader('Cache-Control', 'public, s-maxage=3600, stale-while-revalidate=86400');
  res.status(200).send(`<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join('\n')}
</urlset>
`);
}

function xmlUrl(location: string, lastModified: string | null) {
  const lastmod = lastModified ? `\n    <lastmod>${escapeXml(lastModified)}</lastmod>` : '';
  return `  <url>\n    <loc>${escapeXml(location)}</loc>${lastmod}\n  </url>`;
}

function slug(value: string) {
  return encodeURIComponent(
    value
      .trim()
      .replace(/\s+/g, '-')
      .replace(/[^\p{Letter}\p{Number}-]+/gu, '')
      .slice(0, 80),
  );
}

function escapeXml(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
}
