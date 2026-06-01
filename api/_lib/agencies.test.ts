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
      gov_tier_label: '기초자치단체',
      branch: 'admin',
      branch_label: '집행기관',
      jurisdiction_type: 'autonomous_gu',
      jurisdiction_type_label: '자치구',
      expansion_phase: null,
      expansion_phase_label: null,
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
      gov_tier_label: '광역자치단체',
      branch: 'council',
      branch_label: '의회',
      jurisdiction_type: 'special_city',
      jurisdiction_type_label: '특별시',
      expansion_phase: null,
      expansion_phase_label: null,
    });
  });

  it('preserves Korean labels from the database view when present', () => {
    expect(
      normalizeAgencyRow({
        id: 'agency-3',
        short_name: '경기도청',
        gov_tier: 'regional',
        gov_tier_label: '광역',
        branch: 'admin',
        branch_label: '집행부',
        jurisdiction_type: 'province',
        jurisdiction_type_label: '도',
      }),
    ).toEqual({
      id: 'agency-3',
      short_name: '경기도청',
      gov_tier: 'regional',
      gov_tier_label: '광역',
      branch: 'admin',
      branch_label: '집행부',
      jurisdiction_type: 'province',
      jurisdiction_type_label: '도',
      expansion_phase: null,
      expansion_phase_label: null,
    });
  });

  it('adds Korean labels for source registry priority groups', () => {
    expect(
      normalizeAgencyRow({
        id: 'agency-priority',
        short_name: '행정안전부',
        expansion_phase: 'p2',
      }),
    ).toMatchObject({
      expansion_phase: 'p2',
      expansion_phase_label: 'P2 중앙행정기관·독립기관',
    });
  });

  it('adds Korean labels for special self-governing jurisdictions', () => {
    expect(
      normalizeAgencyRow({
        id: 'agency-4',
        short_name: '세종시청',
        gov_tier: 'regional',
        branch: 'admin',
        jurisdiction_type: 'special_self_governing_city',
      }),
    ).toMatchObject({
      jurisdiction_type: 'special_self_governing_city',
      jurisdiction_type_label: '특별자치시',
    });

    expect(
      normalizeAgencyRow({
        id: 'agency-5',
        short_name: '강원특별자치도청',
        gov_tier: 'regional',
        branch: 'admin',
        jurisdiction_type: 'special_self_governing_province',
      }),
    ).toMatchObject({
      jurisdiction_type: 'special_self_governing_province',
      jurisdiction_type_label: '특별자치도',
    });
  });

  it('adds Korean labels for central/constitutional/public institution taxonomy', () => {
    expect(
      normalizeAgencyRow({
        id: 'agency-6',
        short_name: '행정안전부',
        gov_tier: 'national',
        branch: 'admin',
        jurisdiction_type: 'central_administrative_agency',
      }),
    ).toMatchObject({
      gov_tier_label: '국가기관',
      branch_label: '집행기관',
      jurisdiction_type_label: '중앙행정기관',
    });

    expect(
      normalizeAgencyRow({
        id: 'agency-7',
        short_name: '헌법재판소',
        gov_tier: 'constitutional',
        branch: 'constitutional',
        jurisdiction_type: 'constitutional_institution',
      }),
    ).toMatchObject({
      gov_tier_label: '헌법기관',
      branch_label: '헌법기관',
      jurisdiction_type_label: '헌법기관',
    });

    expect(
      normalizeAgencyRow({
        id: 'agency-8',
        short_name: '감사원',
        gov_tier: 'national',
        branch: 'admin',
        jurisdiction_type: 'independent_state_agency',
      }),
    ).toMatchObject({
      gov_tier_label: '국가기관',
      branch_label: '집행기관',
      jurisdiction_type_label: '독립국가기관',
    });

    expect(
      normalizeAgencyRow({
        id: 'agency-9',
        short_name: '국민연금공단',
        gov_tier: 'public',
        branch: 'public',
        jurisdiction_type: 'public_institution',
      }),
    ).toMatchObject({
      gov_tier_label: '공공기관',
      branch_label: '공공기관',
      jurisdiction_type_label: '지정 공공기관',
    });

    expect(
      normalizeAgencyRow({
        id: 'agency-10',
        short_name: '서울교통공사',
        gov_tier: 'local_public',
        branch: 'public',
        jurisdiction_type: 'local_public_institution',
      }),
    ).toMatchObject({
      gov_tier_label: '지방공공기관',
      branch_label: '공공기관',
      jurisdiction_type_label: '지방공공기관',
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
