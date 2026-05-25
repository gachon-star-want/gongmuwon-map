import { describe, expect, it } from 'vitest';
import { defaultGrades, parseQueryState, normalizeQueryState, serializeQueryState } from './queryState';

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
