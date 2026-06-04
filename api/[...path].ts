import type { VercelRequest, VercelResponse } from '@vercel/node';
import { sendJson } from './_lib/http';
import apiAuthLogin from './auth/login';
import apiAuthLogout from './auth/logout';
import apiAuthMe from './auth/me';
import apiAuthRegister from './auth/register';
import apiCommunityPosts from './community/posts';
import apiCommunityPostComments from './community/posts/[id]/comments';
import apiClosureReport from './closure-report';
import apiCronRecomputeGrades from './cron/recompute-grades';
import apiPlaces from './v1/places';
import apiPlacesSearch from './v1/places/search';
import apiPlacesById from './v1/places/[id]';
import apiPlaceReactions from './v1/places/[id]/reactions';
import apiPlaceVisits from './v1/places/[id]/visits';
import apiRegions from './v1/regions';
import apiStatsSummary from './v1/stats/summary';
import apiAgencies from './v1/agencies';
import apiAgencyById from './v1/agencies/[id]';
import apiSitemap from './sitemap';
import apiTakedownRequest from './takedown-request';

type ApiHandler = (req: VercelRequest, res: VercelResponse) => Promise<void>;

type RouteEntry = { handler: ApiHandler; hasId?: boolean };

const routeTable: [string[], RouteEntry][] = [
  [['community', 'posts'], { handler: apiCommunityPosts }],
  [['community', 'posts', ':id', 'comments'], { handler: apiCommunityPostComments, hasId: true }],

  [['auth', 'login'], { handler: apiAuthLogin }],
  [['auth', 'logout'], { handler: apiAuthLogout }],
  [['auth', 'me'], { handler: apiAuthMe }],
  [['auth', 'register'], { handler: apiAuthRegister }],

  [['v1', 'agencies'], { handler: apiAgencies }],
  [['v1', 'agencies', ':id'], { handler: apiAgencyById, hasId: true }],
  [['v1', 'places', 'search'], { handler: apiPlacesSearch }],
  [['v1', 'places'], { handler: apiPlaces }],
  [['v1', 'places', ':id', 'reactions'], { handler: apiPlaceReactions, hasId: true }],
  [['v1', 'places', ':id', 'visits'], { handler: apiPlaceVisits, hasId: true }],
  [['v1', 'places', ':id'], { handler: apiPlacesById, hasId: true }],
  [['v1', 'regions'], { handler: apiRegions }],
  [['v1', 'stats', 'summary'], { handler: apiStatsSummary }],

  [['sitemap'], { handler: apiSitemap }],
  [['cron', 'recompute-grades'], { handler: apiCronRecomputeGrades }],
  [['closure-report'], { handler: apiClosureReport }],
  [['takedown-request'], { handler: apiTakedownRequest }],
];

export function withId(handler: ApiHandler, req: VercelRequest, res: VercelResponse, id: string) {
  const originalQuery = req.query;
  req.query = { ...originalQuery, id };
  try {
    return handler(req, res);
  } finally {
    req.query = originalQuery;
  }
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const pathname = new URL(req.url ?? '/', 'https://gongmuwon.internal').pathname;
  const routedPath = Array.isArray(req.query.path) ? req.query.path.join('/') : req.query.path;
  const segments = (routedPath ?? pathname.replace(/^\/api\/?/, '')).split('/').filter(Boolean);

  for (const [pattern, { handler: routeHandler, hasId }] of routeTable) {
    if (pattern.length !== segments.length) continue;

    let match = true;
    let idValue: string | undefined;

    for (let i = 0; i < pattern.length; i++) {
      if (pattern[i] === ':id') {
        idValue = segments[i];
      } else if (pattern[i] !== segments[i]) {
        match = false;
        break;
      }
    }

    if (match) {
      if (hasId) {
        await withId(routeHandler, req, res, idValue!);
      } else {
        await routeHandler(req, res);
      }
      return;
    }
  }

  sendJson(res, 404, { error: 'not_found' });
}
