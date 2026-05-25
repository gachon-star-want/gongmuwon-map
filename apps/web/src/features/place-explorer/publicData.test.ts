import { beforeEach, describe, expect, it, vi } from 'vitest';
import { API_BASE, loadPlaceById, loadPlaces, loadRegions, loadVisits, searchPlaces } from './publicData';
import type { PlaceQueryState } from './queryState';
import type { Grade } from './types';

function createJsonResponse(data: unknown): Response {
  return {
    ok: true,
    json: () => Promise.resolve(data),
  } as Response;
}

describe('publicData', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('loads places list from /api/v1/places with grade bbox limit', async () => {
    const mockResponse = [{ id: '1', name: 'a' }];
    const fetchMock = vi.fn() as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue(createJsonResponse(mockResponse));
    vi.stubGlobal('fetch', fetchMock);

    const query: { grade: Grade[] } = {
      grade: ['★★★', '★★', '✦'],
    };
    await loadPlaces(query);

    const calledUrl = (fetchMock.mock.calls[0]?.[0] ?? '') as string;
    expect(calledUrl).toBe(`${API_BASE}/api/v1/places?bbox=37.413%2C126.734%2C37.715%2C127.269&grade=%E2%98%85%E2%98%85%E2%98%85%2C%E2%98%85%E2%98%85%2C%E2%9C%A6&limit=500`);
  });

  it('loads search results with q and region', async () => {
    const mockData = { items: [], next_cursor: null, source_notice: 'ok' };
    const fetchMock = vi.fn() as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue(createJsonResponse(mockData));
    vi.stubGlobal('fetch', fetchMock);

    const query: PlaceQueryState = {
      q: '카페',
      region: ['서울 강남구'],
      grade: ['★★★'],
      sort: 'score',
      placeId: null,
    };
    await loadRegions();

    await searchPlaces(query);
    const calledUrl = (fetchMock.mock.calls[1]?.[0] ?? '') as string;
    expect(calledUrl).toContain('/api/v1/places/search?');
    expect(calledUrl).toContain('q=%EC%B9%B4%ED%8E%98');
    expect(calledUrl).toContain('region=%EC%84%9C%EC%9A%B8+%EA%B0%95%EB%82%A8%EA%B5%AC');
    expect(calledUrl).toContain('grade=%E2%98%85%E2%98%85%E2%98%85');
    expect(calledUrl).toContain('sort=score');
    expect(calledUrl).toContain('limit=100');
  });

  it('loads regions, place by id, and visits', async () => {
    const regions = { items: [], source_notice: 'ok' };
    const place = { id: 'p1', name: 'Place 1' };
    const visits: unknown[] = [];

    const fetchMock = (vi.fn() as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(regions),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(place),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(visits),
      } as Response);
    vi.stubGlobal('fetch', fetchMock);

    expect(await loadRegions()).toEqual([]);
    expect(await loadPlaceById('p1')).toEqual(place);
    expect(await loadVisits('p1')).toEqual(visits);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect((fetchMock.mock.calls[1]?.[0] ?? '')).toContain('/api/v1/places/p1');
    expect((fetchMock.mock.calls[2]?.[0] ?? '')).toContain('/api/v1/places/p1/visits?limit=50');
  });
});
