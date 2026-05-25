import type { VercelRequest, VercelResponse } from '@vercel/node';
import { readQuery } from '../_lib/db';
import { publicReadRoute } from '../_lib/route';
import { CAPITAL_AREA_REGION_METADATA, fallbackRegionMeta } from '../_lib/region-registry';
import { stringParam } from '../_lib/http';

const SOURCE_NOTICE = '공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외';

type RegionItem = {
  region: string;
  label: string;
  place_count: number;
  top_place_count: number;
  recommended_place_count: number;
  new_place_count: number;
  center: {
    latitude: number;
    longitude: number;
  };
  bbox: {
    min_latitude: number;
    min_longitude: number;
    max_latitude: number;
    max_longitude: number;
  };
  last_visit_at: string | null;
};

export default publicReadRoute(async function handler(req: VercelRequest, res: VercelResponse) {
  const includeEmpty = stringParam(req.query.include_empty) === 'true' || stringParam(req.query.include_empty) === '1';
  const { rows } = await readQuery<{
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
  const regionKeys = includeEmpty ? Object.keys(CAPITAL_AREA_REGION_METADATA) : rows.map((row) => row.region).filter((region) => Boolean(region));
  const rawItems = regionKeys
    .filter((region) => includeEmpty || counts.has(region))
    .sort()
    .map((region): RegionItem | null => {
      const meta = includeEmpty ? CAPITAL_AREA_REGION_METADATA[region] : fallbackRegionMeta(region);
      if (!meta) {
        return null;
      }
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

  const items = rawItems.filter((item): item is RegionItem => item !== null);

  return {
    items,
    source_notice: SOURCE_NOTICE,
  };
}, { cache: 'public, s-maxage=1800, stale-while-revalidate=3600' });
