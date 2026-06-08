import type { Place, PlaceReactionSummary, Region, RegionsResponse, SearchResponse, Visit } from './types';
import type { PlaceQueryState } from './queryState';

export const API_BASE = import.meta.env.VITE_API_BASE ?? '';

function apiUrl(path: string) {
  return `${API_BASE}${path}`;
}

function safeClone<T>(obj: T): T {
  if (typeof structuredClone === 'function') {
    return structuredClone(obj);
  }
  return JSON.parse(JSON.stringify(obj));
}

type CacheEntry<T> = {
  data: T;
  expiry: number;
};

const cacheStore: Record<string, CacheEntry<any>> = {};
const inFlightRequests: Record<string, Promise<any> | undefined> = {};

export function clearPublicDataCache() {
  for (const key in cacheStore) {
    delete cacheStore[key];
  }
  for (const key in inFlightRequests) {
    delete inFlightRequests[key];
  }
}

const REGIONS_TTL = 24 * 60 * 60 * 1000; // 24 hours
const PLACES_TTL = 5 * 60 * 1000;       // 5 minutes
const SEARCH_TTL = 5 * 60 * 1000;       // 5 minutes
const PLACE_DETAIL_TTL = 30 * 60 * 1000; // 30 minutes
const VISITS_TTL = 30 * 60 * 1000;       // 30 minutes

async function fetchWithCache<T>(
  url: string,
  ttlMs: number,
  errorName: string,
  init?: RequestInit & { signal?: AbortSignal },
): Promise<T> {
  const signal = init?.signal;

  if (signal?.aborted) {
    throw new DOMException('The user aborted a request.', 'AbortError');
  }

  const cacheKey = url;
  const cached = cacheStore[cacheKey];
  if (cached && cached.expiry > Date.now()) {
    return safeClone(cached.data);
  }

  const activePromise = inFlightRequests[cacheKey];
  if (activePromise !== undefined) {
    try {
      const data = await activePromise;
      if (signal?.aborted) {
        throw new DOMException('The user aborted a request.', 'AbortError');
      }
      return safeClone(data);
    } catch (err) {
      if (signal?.aborted) {
        throw new DOMException('The user aborted a request.', 'AbortError');
      }
      throw err;
    }
  }

  const fetchPromise = (async () => {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${errorName} ${response.status}`);
    const data = await response.json();
    cacheStore[cacheKey] = {
      data,
      expiry: Date.now() + ttlMs,
    };
    return data;
  })();

  inFlightRequests[cacheKey] = fetchPromise;

  const cleanUp = () => {
    delete inFlightRequests[cacheKey];
  };
  fetchPromise.then(cleanUp, cleanUp);

  try {
    const data = await fetchPromise;
    if (signal?.aborted) {
      throw new DOMException('The user aborted a request.', 'AbortError');
    }
    return safeClone(data);
  } catch (err) {
    if (signal?.aborted) {
      throw new DOMException('The user aborted a request.', 'AbortError');
    }
    throw err;
  }
}

export function quantizeBbox(bbox: [number, number, number, number]): [number, number, number, number] {
  return bbox.map((val) => Number(val.toFixed(3))) as [number, number, number, number];
}

export async function loadPlaces(
  query: Pick<PlaceQueryState, 'grade'>,
  bbox?: [number, number, number, number],
  signal?: AbortSignal,
): Promise<Place[]> {
  const params = new URLSearchParams({
    grade: query.grade.join(','),
    limit: bbox ? '300' : '500',
  });
  if (bbox) {
    const quantized = quantizeBbox(bbox);
    params.set('bbox', quantized.join(','));
  }
  const url = apiUrl(`/api/v1/places?${params.toString()}`);
  return fetchWithCache<Place[]>(url, PLACES_TTL, 'places', { signal });
}

export async function searchPlaces(query: PlaceQueryState, signal?: AbortSignal): Promise<SearchResponse> {
  if (query.q !== null && query.q !== undefined && query.q.trim().length < 2) {
    return {
      items: [],
      next_cursor: null,
      source_notice: '',
    };
  }
  const params = new URLSearchParams({
    limit: '100',
    sort: query.sort,
    grade: query.grade.join(','),
  });
  if (query.q) params.set('q', query.q);
  if (query.region.length) params.set('region', query.region.join(','));
  const url = apiUrl(`/api/v1/places/search?${params.toString()}`);
  return fetchWithCache<SearchResponse>(url, SEARCH_TTL, 'search', { signal });
}

export async function loadRegions(): Promise<Region[]> {
  const url = apiUrl('/api/v1/regions');
  const data = await fetchWithCache<RegionsResponse>(url, REGIONS_TTL, 'regions');
  return data.items;
}

export async function loadPlaceById(placeId: string): Promise<Place> {
  const url = apiUrl(`/api/v1/places/${placeId}`);
  return fetchWithCache<Place>(url, PLACE_DETAIL_TTL, 'place');
}

export async function loadVisits(placeId: string): Promise<Visit[]> {
  const url = apiUrl(`/api/v1/places/${placeId}/visits?limit=50`);
  return fetchWithCache<Visit[]>(url, VISITS_TTL, 'visits');
}

export async function loadPlaceReactions(placeId: string): Promise<PlaceReactionSummary> {
  const response = await fetch(apiUrl(`/api/v1/places/${placeId}/reactions`), { credentials: 'include' });
  if (!response.ok) throw new Error(`reactions ${response.status}`);
  return (await response.json()) as PlaceReactionSummary;
}

export async function setPlaceReaction(placeId: string, reaction: 'like' | 'dislike' | null): Promise<PlaceReactionSummary> {
  const response = await fetch(apiUrl(`/api/v1/places/${placeId}/reactions`), {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reaction }),
  });
  if (!response.ok) throw new Error(`reaction ${response.status}`);
  return (await response.json()) as PlaceReactionSummary;
}
