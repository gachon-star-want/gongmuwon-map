import type { Grade, SortMode } from './types';

export const defaultGrades: Grade[] = ['★★★', '★★', '✦'];

const GRADE_OPTIONS = new Set<Grade>(['★★★', '★★', '★', '✦']);

export type PlaceQueryState = {
  q: string;
  region: string[];
  grade: Grade[];
  sort: SortMode;
  placeId: string | null;
};

type RawSortMode = string | null | SortMode;

export function parseQueryState(search = window.location.search): PlaceQueryState {
  const params = new URLSearchParams(search);
  return normalizeQueryState({
    q: params.get('q') ?? '',
    region: splitList(params.get('region')),
    grade: parseGrades(params.get('grade')),
    sort: parseSort(params.get('sort')),
    placeId: params.get('place'),
  });
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
