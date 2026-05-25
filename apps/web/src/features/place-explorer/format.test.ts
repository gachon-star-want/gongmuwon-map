import { describe, expect, it } from 'vitest';
import type { Place } from './types';
import { formatDate, gradeClass, gradeLabel, markerLabel, shortRegionLabel, sortPlaces } from './format';

describe('format helpers', () => {
  const places: Place[] = [
    {
      id: '1',
      name: 'B',
      road_address: null,
      road_address_part: '서울 강남구',
      latitude: 37,
      longitude: 127,
      category: null,
      is_closed: false,
      closure_report_count: 0,
      score: 4.2,
      grade: '★★',
      last_visit_at: '2026-05-20',
      visit_count_12m: 3,
      unique_department_count_12m: 1,
      unique_agency_count_12m: 1,
      avg_amount_per_person: 12000,
      matched_fields: [],
    },
    {
      id: '2',
      name: 'A',
      road_address: null,
      road_address_part: '경기 수원시',
      latitude: 37,
      longitude: 127,
      category: null,
      is_closed: false,
      closure_report_count: 0,
      score: 6.1,
      grade: '★★★',
      last_visit_at: '2026-05-21',
      visit_count_12m: 2,
      unique_department_count_12m: 4,
      unique_agency_count_12m: 1,
      avg_amount_per_person: 11000,
      matched_fields: [],
    },
    {
      id: '3',
      name: 'C',
      road_address: null,
      road_address_part: '인천 강화군',
      latitude: 37,
      longitude: 127,
      category: null,
      is_closed: false,
      closure_report_count: 0,
      score: 5.5,
      grade: '★',
      last_visit_at: '2026-05-19',
      visit_count_12m: 4,
      unique_department_count_12m: 2,
      unique_agency_count_12m: 1,
      avg_amount_per_person: 13000,
      matched_fields: [],
    },
  ];

  it('sortPlaces by score', () => {
    const sorted = sortPlaces(places, 'score');
    expect(sorted.map((place) => place.id)).toEqual(['2', '3', '1']);
  });

  it('sortPlaces by recent', () => {
    const sorted = sortPlaces(places, 'recent');
    expect(sorted.map((place) => place.id)).toEqual(['2', '1', '3']);
  });

  it('sortPlaces by visits', () => {
    const sorted = sortPlaces(places, 'visits');
    expect(sorted.map((place) => place.id)).toEqual(['3', '1', '2']);
  });

  it('formatDate and labels map', () => {
    expect(formatDate('2026-05-20T14:10:00.000Z')).toBe('2026.05.20');
    expect(gradeLabel('★★★')).toBe('강추');
    expect(markerLabel('★')).toBe('1★');
    expect(gradeClass('✦')).toBe('new');
    expect(shortRegionLabel('서울 강남구')).toBe('강남구');
    expect(shortRegionLabel('경기 수원시')).toBe('수원시');
    expect(shortRegionLabel('인천 강화군')).toBe('강화군');
    expect(shortRegionLabel('부산 해운대구')).toBe('부산 해운대구');
  });
});
