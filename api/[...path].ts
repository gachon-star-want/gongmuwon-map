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

  if (segments[0] === 'community') {
    if (segments[1] === 'posts' && segments.length === 2) {
      await apiCommunityPosts(req, res);
      return;
    }
    if (segments[1] === 'posts' && segments[2] && segments[3] === 'comments' && segments.length === 4) {
      await withId(apiCommunityPostComments, req, res, segments[2]);
      return;
    }
  }

  if (segments[0] === 'auth') {
    if (segments[1] === 'login' && segments.length === 2) {
      await apiAuthLogin(req, res);
      return;
    }
    if (segments[1] === 'logout' && segments.length === 2) {
      await apiAuthLogout(req, res);
      return;
    }
    if (segments[1] === 'me' && segments.length === 2) {
      await apiAuthMe(req, res);
      return;
    }
    if (segments[1] === 'register' && segments.length === 2) {
      await apiAuthRegister(req, res);
      return;
    }
  }

  if (segments[0] === 'v1') {
    if (segments[1] === 'agencies' && segments.length === 2) {
      await apiAgencies(req, res);
      return;
    }
    if (segments[1] === 'agencies' && segments.length === 3) {
      await withId(apiAgencyById, req, res, segments[2]);
      return;
    }
    if (segments[1] === 'places' && segments[2] === 'search' && segments.length === 3) {
      await apiPlacesSearch(req, res);
      return;
    }
    if (segments[1] === 'places' && segments.length === 2) {
      await apiPlaces(req, res);
      return;
    }
    if (segments[1] === 'places' && segments[2] && segments[3] === 'reactions' && segments.length === 4) {
      await withId(apiPlaceReactions, req, res, segments[2]);
      return;
    }
    if (segments[1] === 'places' && segments[2] && segments[3] === 'visits' && segments.length === 4) {
      await withId(apiPlaceVisits, req, res, segments[2]);
      return;
    }
    if (segments[1] === 'places' && segments.length === 3) {
      await withId(apiPlacesById, req, res, segments[2]);
      return;
    }
    if (segments[1] === 'regions' && segments.length === 2) {
      await apiRegions(req, res);
      return;
    }
    if (segments[1] === 'stats' && segments[2] === 'summary' && segments.length === 3) {
      await apiStatsSummary(req, res);
      return;
    }
  }

  if (segments[0] === 'sitemap' && segments.length === 1) {
    await apiSitemap(req, res);
    return;
  }
  if (segments[0] === 'cron' && segments[1] === 'recompute-grades' && segments.length === 2) {
    await apiCronRecomputeGrades(req, res);
    return;
  }
  if (segments[0] === 'closure-report' && segments.length === 1) {
    await apiClosureReport(req, res);
    return;
  }
  if (segments[0] === 'takedown-request' && segments.length === 1) {
    await apiTakedownRequest(req, res);
    return;
  }

  sendJson(res, 404, { error: 'not_found' });
}
