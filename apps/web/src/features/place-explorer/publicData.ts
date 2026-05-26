import type { Place, PlaceReactionSummary, Region, RegionsResponse, SearchResponse, Visit } from './types';
import type { PlaceQueryState } from './queryState';

export const API_BASE = import.meta.env.VITE_API_BASE ?? '';

const SEOUL_BBOX = '37.413,126.734,37.715,127.269';

function apiUrl(path: string) {
  return `${API_BASE}${path}`;
}

export async function loadPlaces(query: Pick<PlaceQueryState, 'grade'>): Promise<Place[]> {
  const params = new URLSearchParams({
    bbox: SEOUL_BBOX,
    grade: query.grade.join(','),
    limit: '500',
  });
  const response = await fetch(apiUrl(`/api/v1/places?${params.toString()}`));
  if (!response.ok) throw new Error(`places ${response.status}`);
  return (await response.json()) as Place[];
}

export async function searchPlaces(query: PlaceQueryState, signal?: AbortSignal): Promise<SearchResponse> {
  const params = new URLSearchParams({
    limit: '100',
    sort: query.sort,
    grade: query.grade.join(','),
  });
  if (query.q) params.set('q', query.q);
  if (query.region.length) params.set('region', query.region.join(','));
  const response = await fetch(apiUrl(`/api/v1/places/search?${params.toString()}`), {
    ...(signal ? { signal } : {}),
  } as RequestInit);
  if (!response.ok) throw new Error(`search ${response.status}`);
  return (await response.json()) as SearchResponse;
}

export async function loadRegions(): Promise<Region[]> {
  const response = await fetch(apiUrl('/api/v1/regions'));
  if (!response.ok) throw new Error(`regions ${response.status}`);
  const data = (await response.json()) as RegionsResponse;
  return data.items;
}

export async function loadPlaceById(placeId: string): Promise<Place> {
  const response = await fetch(apiUrl(`/api/v1/places/${placeId}`));
  if (!response.ok) throw new Error(`place ${response.status}`);
  return (await response.json()) as Place;
}

export async function loadVisits(placeId: string): Promise<Visit[]> {
  const response = await fetch(apiUrl(`/api/v1/places/${placeId}/visits?limit=50`));
  if (!response.ok) throw new Error(`visits ${response.status}`);
  return (await response.json()) as Visit[];
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
