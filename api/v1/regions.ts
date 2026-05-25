import type { VercelRequest, VercelResponse } from '@vercel/node';
import { query } from '../_lib/db';
import { methodGuard, sendJson, stringParam } from '../_lib/http';

const SOURCE_NOTICE = '공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외';

type RegionMeta = {
  label: string;
  center: { latitude: number; longitude: number };
  bbox: {
    min_latitude: number;
    min_longitude: number;
    max_latitude: number;
    max_longitude: number;
  };
};

const SEOUL_REGIONS: Record<string, RegionMeta> = {
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

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (!methodGuard(req, res, ['GET'])) return;

  const includeEmpty = stringParam(req.query.include_empty) === 'true' || stringParam(req.query.include_empty) === '1';
  const { rows } = await query<{
    region: string;
    place_count: string;
    top_place_count: string;
    recommended_place_count: string;
    new_place_count: string;
    last_visit_at: string | null;
  }>(
    `
    SELECT
      road_address_part AS region,
      COUNT(*)::text AS place_count,
      COUNT(*) FILTER (WHERE grade = '★★★')::text AS top_place_count,
      COUNT(*) FILTER (WHERE grade = '★★')::text AS recommended_place_count,
      COUNT(*) FILTER (WHERE grade = '✦')::text AS new_place_count,
      MAX(last_visit_at)::text AS last_visit_at
    FROM public.places_public
    WHERE road_address_part IS NOT NULL
    GROUP BY road_address_part
    ORDER BY road_address_part
    `,
  );

  const counts = new Map(rows.map((row) => [row.region, row]));
  const regionKeys = includeEmpty ? Object.keys(SEOUL_REGIONS) : rows.map((row) => row.region).filter((region) => SEOUL_REGIONS[region]);
  const items = regionKeys
    .filter((region) => SEOUL_REGIONS[region] || counts.has(region))
    .sort()
    .map((region) => {
      const meta =
        SEOUL_REGIONS[region] ?? {
          label: region.replace(/^서울\s*/, ''),
          center: { latitude: 37.5665, longitude: 126.978 },
          bbox: { min_latitude: 37.413, min_longitude: 126.734, max_latitude: 37.715, max_longitude: 127.269 },
        };
      const row = counts.get(region);
      return {
        region,
        label: meta.label,
        place_count: Number(row?.place_count ?? 0),
        top_place_count: Number(row?.top_place_count ?? 0),
        recommended_place_count: Number(row?.recommended_place_count ?? 0),
        new_place_count: Number(row?.new_place_count ?? 0),
        center: meta.center,
        bbox: meta.bbox,
        last_visit_at: row?.last_visit_at ?? null,
      };
    });

  sendJson(
    res,
    200,
    {
      items,
      source_notice: SOURCE_NOTICE,
    },
    'public, s-maxage=1800, stale-while-revalidate=3600',
  );
}
