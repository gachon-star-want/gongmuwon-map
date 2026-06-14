import { readQuery } from '../../_lib/db';
import { publicReadRoute } from '../../_lib/route';
import { numberParam, stringParam } from '../../_lib/http';

const SOURCE_NOTICE = '공공누리 제1유형 · 출처: 국가데이터처 SGIS, 통계청 KOSIS';
const HOUSEHOLD_SIZES = new Set([1, 2, 3, 4]);

type RankRow = {
  adm_cd: string;
  name: string;
  score: string;
  rank_in_sigungu: number;
  sigungu_emd_count: number;
  solo_ratio: string | null;
};

// 시군구 하위 읍면동을 가구원수별 거주적합도 점수로 랭킹 (ADR-015: 시군구 내 상대평가)
export default publicReadRoute(async ({ req }) => {
  const admCd = stringParam(req.query.adm_cd);
  if (!admCd || !/^\d{5}$/.test(admCd)) {
    return { status: 400, body: { error: 'adm_cd_required', detail: '시군구 5자리 코드가 필요합니다' } };
  }
  const householdRaw = numberParam(req.query.household, 1);
  const household = HOUSEHOLD_SIZES.has(householdRaw) ? householdRaw : 1;
  const profile = numberParam(req.query.profile, 1);

  const { rows } = await readQuery<RankRow>(
    `SELECT s.adm_cd, r.name, s.score::text AS score, s.rank_in_sigungu, s.sigungu_emd_count,
            solo.value::text AS solo_ratio
     FROM public.neighborhood_scores_v1 s
     JOIN public.adm_regions r ON r.adm_cd = s.adm_cd
     LEFT JOIN public.neighborhood_metrics solo
       ON solo.adm_cd = s.adm_cd AND solo.metric_key = 'solo_household_ratio' AND solo.household_size = 0
     WHERE s.parent_cd = $1 AND s.household_size = $2 AND s.profile_version = $3
     ORDER BY s.rank_in_sigungu`,
    [admCd, household, profile],
  );

  const items = rows.map((row) => ({
    adm_cd: row.adm_cd,
    name: row.name,
    score: Number(row.score),
    rank: row.rank_in_sigungu,
    total: row.sigungu_emd_count,
    solo_household_ratio: row.solo_ratio === null ? null : Number(row.solo_ratio),
  }));

  return { household, items, source_notice: SOURCE_NOTICE };
}, { cache: 'public, s-maxage=3600, stale-while-revalidate=86400' });
