type ParentRegion = '서울' | '경기' | '인천';
type JurisdictionType = 'special_city' | 'metro_city' | 'province' | 'autonomous_gu' | 'si' | 'gun';

export type PublicRegionMeta = {
  region: string;
  label: string;
  parent_region: ParentRegion;
  jurisdiction_type: JurisdictionType;
  center: { latitude: number; longitude: number };
  bbox: {
    min_latitude: number;
    min_longitude: number;
    max_latitude: number;
    max_longitude: number;
  };
  estimated: boolean;
  metadata_source: 'exact' | 'parent_region_fallback';
};

type SeoulBaseMeta = {
  label: string;
  center: { latitude: number; longitude: number };
  bbox: {
    min_latitude: number;
    min_longitude: number;
    max_latitude: number;
    max_longitude: number;
  };
};

const SEOUL_BASE_META: Record<string, SeoulBaseMeta> = {
  '서울 강남구': {
    label: '강남구',
    center: { latitude: 37.5172, longitude: 127.0473 },
    bbox: { min_latitude: 37.456, min_longitude: 127.01, max_latitude: 37.535, max_longitude: 127.125 },
  },
  '서울 강동구': {
    label: '강동구',
    center: { latitude: 37.5301, longitude: 127.1238 },
    bbox: { min_latitude: 37.515, min_longitude: 127.102, max_latitude: 37.57, max_longitude: 127.183 },
  },
  '서울 강북구': {
    label: '강북구',
    center: { latitude: 37.6396, longitude: 127.0257 },
    bbox: { min_latitude: 37.611, min_longitude: 126.983, max_latitude: 37.701, max_longitude: 127.047 },
  },
  '서울 강서구': {
    label: '강서구',
    center: { latitude: 37.5509, longitude: 126.8495 },
    bbox: { min_latitude: 37.529, min_longitude: 126.764, max_latitude: 37.585, max_longitude: 126.886 },
  },
  '서울 관악구': {
    label: '관악구',
    center: { latitude: 37.4784, longitude: 126.9516 },
    bbox: { min_latitude: 37.435, min_longitude: 126.903, max_latitude: 37.495, max_longitude: 126.987 },
  },
  '서울 광진구': {
    label: '광진구',
    center: { latitude: 37.5384, longitude: 127.0823 },
    bbox: { min_latitude: 37.525, min_longitude: 127.057, max_latitude: 37.572, max_longitude: 127.116 },
  },
  '서울 구로구': {
    label: '구로구',
    center: { latitude: 37.4955, longitude: 126.8877 },
    bbox: { min_latitude: 37.463, min_longitude: 126.823, max_latitude: 37.518, max_longitude: 126.91 },
  },
  '서울 금천구': {
    label: '금천구',
    center: { latitude: 37.4569, longitude: 126.8955 },
    bbox: { min_latitude: 37.433, min_longitude: 126.875, max_latitude: 37.484, max_longitude: 126.921 },
  },
  '서울 노원구': {
    label: '노원구',
    center: { latitude: 37.6542, longitude: 127.0568 },
    bbox: { min_latitude: 37.615, min_longitude: 127.035, max_latitude: 37.694, max_longitude: 127.106 },
  },
  '서울 도봉구': {
    label: '도봉구',
    center: { latitude: 37.6688, longitude: 127.0471 },
    bbox: { min_latitude: 37.646, min_longitude: 127.01, max_latitude: 37.701, max_longitude: 127.065 },
  },
  '서울 동대문구': {
    label: '동대문구',
    center: { latitude: 37.5744, longitude: 127.0396 },
    bbox: { min_latitude: 37.559, min_longitude: 127.024, max_latitude: 37.607, max_longitude: 127.075 },
  },
  '서울 동작구': {
    label: '동작구',
    center: { latitude: 37.5124, longitude: 126.9393 },
    bbox: { min_latitude: 37.476, min_longitude: 126.914, max_latitude: 37.517, max_longitude: 126.982 },
  },
  '서울 마포구': {
    label: '마포구',
    center: { latitude: 37.5663, longitude: 126.9016 },
    bbox: { min_latitude: 37.54, min_longitude: 126.858, max_latitude: 37.586, max_longitude: 126.956 },
  },
  '서울 서대문구': {
    label: '서대문구',
    center: { latitude: 37.5791, longitude: 126.9368 },
    bbox: { min_latitude: 37.558, min_longitude: 126.91, max_latitude: 37.611, max_longitude: 126.968 },
  },
  '서울 서초구': {
    label: '서초구',
    center: { latitude: 37.4837, longitude: 127.0324 },
    bbox: { min_latitude: 37.425, min_longitude: 126.982, max_latitude: 37.523, max_longitude: 127.092 },
  },
  '서울 성동구': {
    label: '성동구',
    center: { latitude: 37.5633, longitude: 127.0369 },
    bbox: { min_latitude: 37.536, min_longitude: 127.008, max_latitude: 37.572, max_longitude: 127.072 },
  },
  '서울 성북구': {
    label: '성북구',
    center: { latitude: 37.5894, longitude: 127.0167 },
    bbox: { min_latitude: 37.573, min_longitude: 126.977, max_latitude: 37.637, max_longitude: 127.052 },
  },
  '서울 송파구': {
    label: '송파구',
    center: { latitude: 37.5145, longitude: 127.1059 },
    bbox: { min_latitude: 37.476, min_longitude: 127.069, max_latitude: 37.535, max_longitude: 127.167 },
  },
  '서울 양천구': {
    label: '양천구',
    center: { latitude: 37.5169, longitude: 126.8664 },
    bbox: { min_latitude: 37.502, min_longitude: 126.819, max_latitude: 37.546, max_longitude: 126.887 },
  },
  '서울 영등포구': {
    label: '영등포구',
    center: { latitude: 37.5264, longitude: 126.8963 },
    bbox: { min_latitude: 37.491, min_longitude: 126.878, max_latitude: 37.556, max_longitude: 126.94 },
  },
  '서울 용산구': {
    label: '용산구',
    center: { latitude: 37.5326, longitude: 126.9905 },
    bbox: { min_latitude: 37.515, min_longitude: 126.955, max_latitude: 37.556, max_longitude: 127.024 },
  },
  '서울 은평구': {
    label: '은평구',
    center: { latitude: 37.6027, longitude: 126.9291 },
    bbox: { min_latitude: 37.58, min_longitude: 126.885, max_latitude: 37.657, max_longitude: 126.966 },
  },
  '서울 종로구': {
    label: '종로구',
    center: { latitude: 37.5735, longitude: 126.9788 },
    bbox: { min_latitude: 37.565, min_longitude: 126.94, max_latitude: 37.632, max_longitude: 127.024 },
  },
  '서울 중구': {
    label: '중구',
    center: { latitude: 37.5636, longitude: 126.9976 },
    bbox: { min_latitude: 37.544, min_longitude: 126.969, max_latitude: 37.571, max_longitude: 127.026 },
  },
  '서울 중랑구': {
    label: '중랑구',
    center: { latitude: 37.6063, longitude: 127.0927 },
    bbox: { min_latitude: 37.585, min_longitude: 127.073, max_latitude: 37.625, max_longitude: 127.116 },
  },
};

const GYEONGGI_CITIES = [
  '수원시',
  '성남시',
  '의정부시',
  '안양시',
  '부천시',
  '광명시',
  '평택시',
  '동두천시',
  '안산시',
  '고양시',
  '과천시',
  '구리시',
  '남양주시',
  '오산시',
  '시흥시',
  '군포시',
  '의왕시',
  '하남시',
  '용인시',
  '파주시',
  '이천시',
  '안성시',
  '김포시',
  '화성시',
  '광주시',
  '양주시',
  '포천시',
  '여주시',
];

const GYEONGGI_COUNTIES = ['연천군', '가평군', '양평군'];

const INCHEON_GUS = ['중구', '동구', '미추홀구', '연수구', '남동구', '부평구', '계양구', '서구'];
const INCHEON_COUNTIES = ['강화군', '옹진군'];

const PARENT_REGION_FALLBACK_META: Record<ParentRegion, Omit<PublicRegionMeta, 'region' | 'label' | 'jurisdiction_type'>> = {
  서울: {
    parent_region: '서울',
    center: { latitude: 37.5665, longitude: 126.978 },
    bbox: { min_latitude: 37.413, min_longitude: 126.734, max_latitude: 37.715, max_longitude: 127.269 },
    estimated: true,
    metadata_source: 'parent_region_fallback',
  },
  경기: {
    parent_region: '경기',
    center: { latitude: 37.275, longitude: 127.2 },
    bbox: { min_latitude: 36.9, min_longitude: 126.5, max_latitude: 38.4, max_longitude: 129.2 },
    estimated: true,
    metadata_source: 'parent_region_fallback',
  },
  인천: {
    parent_region: '인천',
    center: { latitude: 37.4563, longitude: 126.7052 },
    bbox: { min_latitude: 36.9, min_longitude: 126.2, max_latitude: 37.9, max_longitude: 126.9 },
    estimated: true,
    metadata_source: 'parent_region_fallback',
  },
};

function normalizeRegion(region: string) {
  return region.trim().replace(/\s+/g, ' ');
}

function makeRegionMeta(
  region: string,
  parentRegion: ParentRegion,
  jurisdictionType: JurisdictionType,
  center: { latitude: number; longitude: number },
  bbox: { min_latitude: number; min_longitude: number; max_latitude: number; max_longitude: number },
  estimated: boolean,
  metadataSource: 'exact' | 'parent_region_fallback',
): PublicRegionMeta {
  return {
    region,
    label: region.replace(/^[^ ]+ /, ''),
    parent_region: parentRegion,
    jurisdiction_type: jurisdictionType,
    center,
    bbox,
    estimated,
    metadata_source: metadataSource,
  };
}

function splitRegion(region: string): { parent: ParentRegion; local: string } | null {
  const match = normalizeRegion(region).match(/^(서울특별시|서울|경기도|경기|인천광역시|인천)\s+(.+)$/);
  if (!match) return null;

  const [, rawParent, local] = match;
  const parent: ParentRegion =
    rawParent === '서울특별시' || rawParent === '서울'
      ? '서울'
      : rawParent === '경기도' || rawParent === '경기'
        ? '경기'
        : '인천';

  return { parent, local };
}

function guessJurisdictionType(parent: ParentRegion, local: string): JurisdictionType {
  const suffix = local.replace(/\s/g, '');
  if (suffix.endsWith('군')) return 'gun';
  if (parent === '서울' || parent === '인천') {
    return 'autonomous_gu';
  }
  return 'si';
};

export const SEOUL_REGION_METADATA: Record<string, PublicRegionMeta> = Object.fromEntries(
  Object.entries(SEOUL_BASE_META).map(([region, base]) => [
    region,
    makeRegionMeta(
      region,
      '서울',
      'autonomous_gu',
      base.center,
      base.bbox,
      false,
      'exact',
    ),
  ]),
) as Record<string, PublicRegionMeta>;

export const CAPITAL_AREA_REGION_METADATA: Record<string, PublicRegionMeta> = {
  ...SEOUL_REGION_METADATA,
  ...Object.fromEntries(
    [...GYEONGGI_CITIES, ...GYEONGGI_COUNTIES].map((regionName) => {
      const region = `경기 ${regionName}`;
      const jurisdictionType = regionName.endsWith('군') ? 'gun' : 'si';
      return [
        region,
        makeRegionMeta(
          region,
          '경기',
          jurisdictionType,
          PARENT_REGION_FALLBACK_META['경기'].center,
          PARENT_REGION_FALLBACK_META['경기'].bbox,
          true,
          'parent_region_fallback',
        ),
      ];
    }),
  ),
  ...Object.fromEntries(
    [...INCHEON_GUS, ...INCHEON_COUNTIES].map((regionName) => {
      const region = `인천 ${regionName}`;
      const jurisdictionType = regionName.endsWith('군') ? 'gun' : 'autonomous_gu';
      return [
        region,
        makeRegionMeta(
          region,
          '인천',
          jurisdictionType,
          PARENT_REGION_FALLBACK_META['인천'].center,
          PARENT_REGION_FALLBACK_META['인천'].bbox,
          true,
          'parent_region_fallback',
        ),
      ];
    }),
  ),
} as Record<string, PublicRegionMeta>;

export function regionLabel(region: string): string {
  const key = normalizeRegion(region);
  return regionMeta(key)?.label || key.replace(/^(서울|경기|인천)\s+/, '');
}

export function regionMeta(region: string): PublicRegionMeta | null {
  return CAPITAL_AREA_REGION_METADATA[normalizeRegion(region)] ?? null;
}

export function fallbackRegionMeta(region: string): PublicRegionMeta {
  const normalized = normalizeRegion(region);
  const exact = regionMeta(normalized);
  if (exact) return exact;

  const split = splitRegion(normalized);
  if (!split) {
    const fallback = PARENT_REGION_FALLBACK_META['서울'];
    return {
      region: normalized,
      label: normalized,
      parent_region: fallback.parent_region,
      jurisdiction_type: 'autonomous_gu',
      center: fallback.center,
      bbox: fallback.bbox,
      estimated: true,
      metadata_source: fallback.metadata_source,
    };
  }

  const parent = split.parent;
  const base = PARENT_REGION_FALLBACK_META[parent];
  return {
    region: normalized,
    label: split.local,
    parent_region: parent,
    jurisdiction_type: guessJurisdictionType(parent, split.local),
    center: base.center,
    bbox: base.bbox,
    estimated: true,
    metadata_source: 'parent_region_fallback',
  };
}
