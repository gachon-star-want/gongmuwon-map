import { describe, expect, it } from 'vitest';
import { CAPITAL_AREA_REGION_METADATA, fallbackRegionMeta, regionLabel, regionMeta } from './region-registry';

describe('region registry', () => {
  it('returns label by stripping parent prefix for metro regions', () => {
    expect(regionLabel('서울 강남구')).toBe('강남구');
    expect(regionLabel('경기 수원시')).toBe('수원시');
    expect(regionLabel('인천 강화군')).toBe('강화군');
  });

  it('returns exact match when region exists in metadata', () => {
    const seoulDistrict = regionMeta('서울 중구');
    const gyeonggiCity = regionMeta('경기 수원시');
    const incheonCounty = regionMeta('인천 강화군');

    expect(seoulDistrict).not.toBeNull();
    expect(seoulDistrict?.estimated).toBe(false);
    expect(seoulDistrict?.metadata_source).toBe('exact');

    expect(gyeonggiCity).not.toBeNull();
    expect(gyeonggiCity?.estimated).toBe(true);
    expect(gyeonggiCity?.metadata_source).toBe('parent_region_fallback');

    expect(incheonCounty).not.toBeNull();
    expect(incheonCounty?.estimated).toBe(true);
  });

  it('returns null for non-existent exact region', () => {
    expect(regionMeta('전북 전주시')).toBeNull();
  });

  it('fallbacks to parent-region metadata when exact match is missing', () => {
    const fallback = fallbackRegionMeta('경기 안양시 만안구');

    expect(fallback.region).toBe('경기 안양시 만안구');
    expect(fallback.label).toBe('안양시 만안구');
    expect(fallback.parent_region).toBe('경기');
    expect(fallback.jurisdiction_type).toBe('si');
    expect(fallback.estimated).toBe(true);
    expect(fallback.metadata_source).toBe('parent_region_fallback');
  });

  it('uses conservative fallback when parent cannot be parsed', () => {
    const fallback = fallbackRegionMeta('임시 구역');

    expect(fallback.region).toBe('임시 구역');
    expect(fallback.label).toBe('임시 구역');
    expect(fallback.parent_region).toBe('서울');
    expect(fallback.estimated).toBe(true);
    expect(fallback.metadata_source).toBe('parent_region_fallback');
  });

  it('contains expected capital-area registry size and key coverage', () => {
    const keys = Object.keys(CAPITAL_AREA_REGION_METADATA);

    expect(keys).toHaveLength(66);
    expect(keys.filter((region) => region.startsWith('서울 '))).toHaveLength(25);
    expect(keys.filter((region) => region.startsWith('경기 '))).toHaveLength(31);
    expect(keys.filter((region) => region.startsWith('인천 '))).toHaveLength(10);
    expect(CAPITAL_AREA_REGION_METADATA['서울 강남구']).toBeDefined();
    expect(CAPITAL_AREA_REGION_METADATA['경기 수원시']).toBeDefined();
    expect(CAPITAL_AREA_REGION_METADATA['경기 가평군']).toBeDefined();
    expect(CAPITAL_AREA_REGION_METADATA['인천 중구']).toBeDefined();
    expect(CAPITAL_AREA_REGION_METADATA['인천 옹진군']).toBeDefined();
  });
});
