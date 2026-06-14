import { readQuery } from '../../_lib/db';
import { publicReadRoute } from '../../_lib/route';
import { numberParam, stringParam } from '../../_lib/http';

const SOURCE_NOTICE = '공공누리 제1유형 · 출처: 국가데이터처 SGIS, 통계청 KOSIS';
const HOUSEHOLD_SIZES = new Set([1, 2, 3, 4]);

// 읍면동 상세: 종합점수 + 지표 raw값(분야·신뢰도) + 가구원수 분포
export default publicReadRoute(async ({ req }) => {
  const admCd = stringParam(req.query.adm_cd);
  if (!admCd || !/^\d{8}$/.test(admCd)) {
    return { status: 400, body: { error: 'adm_cd_required', detail: '읍면동 8자리 코드가 필요합니다' } };
  }
  const householdRaw = numberParam(req.query.household, 1);
  const household = HOUSEHOLD_SIZES.has(householdRaw) ? householdRaw : 1;
  const profile = numberParam(req.query.profile, 1);

  const region = await readQuery<{ adm_cd: string; name: string; full_name: string; parent_cd: string | null }>(
    `SELECT adm_cd, name, full_name, parent_cd FROM public.adm_regions WHERE adm_cd = $1`,
    [admCd],
  );
  if (region.rows.length === 0) {
    return { status: 404, body: { error: 'not_found' } };
  }

  const score = await readQuery<{ score: string; rank_in_sigungu: number; sigungu_emd_count: number; field_count: number }>(
    `SELECT score::text AS score, rank_in_sigungu, sigungu_emd_count, field_count
     FROM public.neighborhood_scores_v1
     WHERE adm_cd = $1 AND household_size = $2 AND profile_version = $3`,
    [admCd, household, profile],
  );

  const metrics = await readQuery<{
    metric_key: string; category: string; display_name: string; unit: string | null;
    value: string; as_of_year: number | null; imputed: boolean;
  }>(
    `SELECT m.metric_key, c.category, c.display_name, c.unit,
            m.value::text AS value, m.as_of_year, m.imputed
     FROM public.neighborhood_metrics m
     JOIN public.metric_catalog c ON c.metric_key = m.metric_key
     WHERE m.adm_cd = $1 AND m.household_size = 0
     ORDER BY c.category, c.display_name`,
    [admCd],
  );

  const distribution = await readQuery<{ household_size: number; value: string }>(
    `SELECT household_size, value::text AS value
     FROM public.neighborhood_metrics
     WHERE adm_cd = $1 AND metric_key = 'household_count'
     ORDER BY household_size`,
    [admCd],
  );

  const sc = score.rows[0];
  return {
    region: region.rows[0],
    household,
    score: sc
      ? { score: Number(sc.score), rank: sc.rank_in_sigungu, total: sc.sigungu_emd_count, fields: sc.field_count }
      : null,
    metrics: metrics.rows.map((m) => ({
      metric_key: m.metric_key,
      category: m.category,
      display_name: m.display_name,
      unit: m.unit,
      value: Number(m.value),
      as_of_year: m.as_of_year,
      imputed: m.imputed,
    })),
    household_distribution: distribution.rows.map((d) => ({ size: d.household_size, households: Number(d.value) })),
    source_notice: SOURCE_NOTICE,
  };
}, { cache: 'public, s-maxage=3600, stale-while-revalidate=86400' });
