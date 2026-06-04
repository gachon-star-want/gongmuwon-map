import type { Grade, SortMode } from './types';

export const defaultGrades: Grade[] = ['★★★', '★★', '✦'];
export const allGrades: Grade[] = ['★★★', '★★', '✦', '★'];

const GRADE_OPTIONS = new Set<Grade>(allGrades);
const PLACE_DETAIL_PATH_PREFIX = '/r/';
const UUID_PLACE_ID_PATTERN = /([0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12})$/;

export type PlaceQueryState = {
  q: string;
  region: string[];
  grade: Grade[];
  sort: SortMode;
  placeId: string | null;
};

type RawSortMode = string | null | SortMode;

export function parseQueryState(
  search = typeof window === 'undefined' ? '' : window.location.search,
  pathname = typeof window === 'undefined' ? '/' : window.location.pathname,
): PlaceQueryState {
  const params = new URLSearchParams(search);
  const pathPlaceId = extractPlaceIdFromRoute(pathname);
  const queryPlaceId = params.get('place');
  return normalizeQueryState({
    q: params.get('q') ?? '',
    region: splitList(params.get('region')),
    grade: parseGrades(params.get('grade')),
    sort: parseSort(params.get('sort')),
    placeId: queryPlaceId ?? pathPlaceId,
  });
}

export function extractPlaceIdFromRoute(pathname: string = typeof window === 'undefined' ? '/' : window.location.pathname): string | null {
  const normalized = (pathname ?? '').endsWith('/') ? pathname.slice(0, -1) : pathname;
  if (!normalized.startsWith(PLACE_DETAIL_PATH_PREFIX)) return null;
  const route = normalized.slice(PLACE_DETAIL_PATH_PREFIX.length);
  if (!route) return null;
  const uuidMatch = route.match(UUID_PLACE_ID_PATTERN);
  if (uuidMatch?.[1]) {
    return uuidMatch[1];
  }
  return null;
}

export function resolveExplorerPathname(pathname: string, state: PlaceQueryState) {
  if (!pathname.startsWith(PLACE_DETAIL_PATH_PREFIX)) return pathname;
  const routePlaceId = extractPlaceIdFromRoute(pathname);
  return routePlaceId && state.placeId === routePlaceId ? pathname : '/';
}

export function normalizeQueryState(state: PlaceQueryState): PlaceQueryState {
  return {
    q: state.q.trim(),
    region: dedupeStrings(state.region.filter(Boolean)),
    grade: normalizeGrades(state.grade),
    sort: parseSort(state.sort),
    placeId: state.placeId || null,
  };
}

export function serializeQueryState(state: PlaceQueryState) {
  const params = new URLSearchParams();
  if (state.q) params.set('q', state.q);
  if (state.region.length) params.set('region', state.region.join(','));
  if (state.grade.length && state.grade.join(',') !== defaultGrades.join(',')) params.set('grade', state.grade.join(','));
  if (state.sort !== 'score') params.set('sort', state.sort);
  if (state.placeId) params.set('place', state.placeId);
  const query = params.toString();
  return query ? `?${query}` : '';
}

export function isDefaultGradeFilter(grades: Grade[]) {
  return grades.join(',') === defaultGrades.join(',');
}

function parseSort(raw: RawSortMode): SortMode {
  return raw === 'recent' || raw === 'visits' || raw === 'score' ? raw : 'score';
}

function parseGrades(raw: string | null): Grade[] {
  const values = splitList(raw).filter((value): value is Grade => GRADE_OPTIONS.has(value as Grade));
  return values;
}

function normalizeGrades(grades: Grade[]): Grade[] {
  const normalized = dedupeValues(grades.filter((grade) => GRADE_OPTIONS.has(grade)));
  return normalized.length ? normalized : defaultGrades;
}

function dedupeValues<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}

function dedupeStrings(values: string[]) {
  return dedupeValues(values);
}

function splitList(raw: string | null) {
  return raw
    ? raw
        .split(',')
        .map((value) => value.trim())
        .filter(Boolean)
    : [];
}
