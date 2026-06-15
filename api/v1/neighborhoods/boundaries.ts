import { readQuery } from '../../_lib/db';
import { publicReadRoute } from '../../_lib/route';
import { numberParam, stringParam } from '../../_lib/http';

const HOUSEHOLD_SIZES = new Set([1, 2, 3, 4]);

type BoundaryRow = {
  adm_cd: string;
  name: string;
  geojson: { type?: string; geometry?: unknown } | unknown;
  score: string | null;
  rank_in_sigungu: number | null;
};

// 시군구 하위 읍면동 경계 + 점수를 한 번에 (choropleth용 FeatureCollection)
export default publicReadRoute(async ({ req }) => {
  const admCd = stringParam(req.query.adm_cd);
  if (!admCd || !/^\d{5}$/.test(admCd)) {
    return { status: 400, body: { error: 'adm_cd_required', detail: '시군구 5자리 코드가 필요합니다' } };
  }
  const householdRaw = numberParam(req.query.household, 1);
  const household = HOUSEHOLD_SIZES.has(householdRaw) ? householdRaw : 1;
  const profile = numberParam(req.query.profile, 1);

  const { rows } = await readQuery<BoundaryRow>(
    `SELECT r.adm_cd, r.name, b.geojson, s.score::text AS score, s.rank_in_sigungu
     FROM public.region_boundaries b
     JOIN public.adm_regions r ON r.adm_cd = b.adm_cd
     LEFT JOIN public.neighborhood_scores_v1 s
       ON s.adm_cd = b.adm_cd AND s.household_size = $2 AND s.profile_version = $3
     WHERE r.parent_cd = $1`,
    [admCd, household, profile],
  );

  const features = rows.map((row) => {
    const stored = row.geojson as { type?: string; geometry?: unknown };
    const geometry = stored && typeof stored === 'object' && 'geometry' in stored ? stored.geometry : stored;
    return {
      type: 'Feature' as const,
      properties: {
        adm_cd: row.adm_cd,
        name: row.name,
        score: row.score === null ? null : Number(row.score),
        rank: row.rank_in_sigungu,
      },
      geometry,
    };
  });

  return { type: 'FeatureCollection', household, features };
}, { cache: 'public, s-maxage=3600, stale-while-revalidate=86400' });
