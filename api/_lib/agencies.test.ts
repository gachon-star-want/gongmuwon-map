import { describe, expect, it } from 'vitest';
import { normalizeAgencyRow, normalizeAgencyRows } from './agencies';

describe('agency row normalization', () => {
  it('maps legacy kind rows to ADR-011 taxonomy fields', () => {
    expect(
      normalizeAgencyRow({
        id: 'agency-1',
        short_name: '은평구청',
        kind: 'gu_office',
      }),
    ).toEqual({
      id: 'agency-1',
      short_name: '은평구청',
      gov_tier: 'basic',
      branch: 'admin',
      jurisdiction_type: 'autonomous_gu',
    });
  });

  it('preserves current taxonomy fields and removes legacy kind', () => {
    expect(
      normalizeAgencyRow({
        id: 'agency-2',
        short_name: '서울시의회',
        kind: 'city_council',
        gov_tier: 'regional',
        branch: 'council',
        jurisdiction_type: 'special_city',
      }),
    ).toEqual({
      id: 'agency-2',
      short_name: '서울시의회',
      gov_tier: 'regional',
      branch: 'council',
      jurisdiction_type: 'special_city',
    });
  });

  it('sorts normalized rows using the public agency ordering', () => {
    const rows = normalizeAgencyRows([
      {
        id: 'regional',
        short_name: '서울시청',
        kind: 'city_hall',
        parent_region: '서울특별시',
        sub_region: null,
      },
      {
        id: 'basic-council',
        short_name: '강남구의회',
        kind: 'gu_council',
        parent_region: '서울특별시',
        sub_region: '강남구',
      },
      {
        id: 'basic-admin',
        short_name: '강남구청',
        kind: 'gu_office',
        parent_region: '서울특별시',
        sub_region: '강남구',
      },
    ]);

    expect(rows.map((row) => row.id)).toEqual(['basic-admin', 'basic-council', 'regional']);
  });
});
