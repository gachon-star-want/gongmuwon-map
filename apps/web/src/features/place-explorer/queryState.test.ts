import { describe, expect, it } from 'vitest';
import {
  defaultGrades,
  extractPlaceIdFromRoute,
  normalizeQueryState,
  parseQueryState,
  resolveExplorerPathname,
  serializeQueryState,
} from './queryState';

describe('queryState', () => {
  it('parseQueryState handles defaults', () => {
    const state = parseQueryState('');
    expect(state).toEqual({
      q: '',
      region: [],
      grade: defaultGrades,
      sort: 'score',
      placeId: null,
    });
  });

  it('round trips query state', () => {
    const raw = parseQueryState('?q=카페&region=서울 강남구&grade=★★★,bad&sort=visits&place=abc');
    const serialized = serializeQueryState(raw);
    expect(serialized).toContain('q=%EC%B9%B4%ED%8E%98');
    expect(serialized).toContain('region=%EC%84%9C%EC%9A%B8+%EA%B0%95%EB%82%A8%EA%B5%AC');
    expect(serialized).toContain('sort=visits');
    expect(serialized).toContain('place=abc');
    expect(serialized).not.toContain('bad');
    expect(raw.grade).toEqual(['★★★']);
  });

  it('parses placeId from /r route path', () => {
    const state = parseQueryState('', '/r/%EC%B0%84%EB%A3%8C-%EB%A1%9C%EC%98%A8-8c5e2f3a-7e8d-4b4a-bb8f-7f2f4f7d2b55');
    expect(state.placeId).toBe('8c5e2f3a-7e8d-4b4a-bb8f-7f2f4f7d2b55');
  });

  it('prefers query place over route-derived placeId', () => {
    const state = parseQueryState('?place=query-id', '/r/slug-9f8a8d8f-0000-4000-8000-111111111111');
    expect(state.placeId).toBe('query-id');
  });

  it('parses placeId from route path with trailing slash', () => {
    expect(extractPlaceIdFromRoute('/r/서울-점심-9f8a8d8f-0000-4000-8000-111111111111/')).toBe(
      '9f8a8d8f-0000-4000-8000-111111111111',
    );
  });

  it('ignores malformed detail route paths without a UUID', () => {
    expect(extractPlaceIdFromRoute('/r/help-please')).toBeNull();
    expect(extractPlaceIdFromRoute('/r/foo-bar-baz')).toBeNull();
  });

  it('preserves valid detail route only while it matches selected place', () => {
    const pathname = '/r/서울-점심-9f8a8d8f-0000-4000-8000-111111111111';
    const state = parseQueryState('', pathname);
    expect(resolveExplorerPathname(pathname, state)).toBe(pathname);
    expect(resolveExplorerPathname(pathname, { ...state, placeId: null })).toBe('/');
    expect(resolveExplorerPathname('/r/help-please', state)).toBe('/');
  });

  it('normalizeQueryState falls back when all grades are invalid', () => {
    const normalized = normalizeQueryState({
      q: '  서울  ',
      region: ['A', 'B', 'A'],
      grade: [] as Array<'★★★' | '★★' | '★' | '✦'>,
      sort: 'score',
      placeId: 'p1',
    });
    expect(normalized).toEqual({
      q: '서울',
      region: ['A', 'B'],
      grade: defaultGrades,
      sort: 'score',
      placeId: 'p1',
    });
  });
});
