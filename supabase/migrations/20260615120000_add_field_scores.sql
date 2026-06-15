-- 분야별 percentile(field_score) 보존 — 강점/약점 칩·지도 렌즈의 전제 (ADR-018)
-- neighborhood_scores_v1은 CTE에서 분야 percentile을 계산하고 최종 SELECT에서 버린다.
-- 같은 산식을 분야(category) 단위로 보존한다. 가구원수 가중치 전(前) 상대치라 household 무관.

CREATE MATERIALIZED VIEW public.neighborhood_field_scores_v1 AS
WITH latest AS (
  SELECT DISTINCT ON (adm_cd, metric_key)
    adm_cd, metric_key, value
  FROM public.neighborhood_metrics
  WHERE household_size = 0 AND value IS NOT NULL
  ORDER BY adm_cd, metric_key, ref_period DESC
),
joined AS (
  SELECT l.adm_cd, r.parent_cd, mc.category, mc.direction, l.metric_key, l.value
  FROM latest l
  JOIN public.metric_catalog mc ON mc.metric_key = l.metric_key
  JOIN public.adm_regions r ON r.adm_cd = l.adm_cd AND r.level = 'emd'
),
norm AS (
  SELECT
    adm_cd, parent_cd, category,
    CASE WHEN direction = 1
      THEN PERCENT_RANK() OVER (PARTITION BY parent_cd, metric_key ORDER BY value)
      ELSE 1 - PERCENT_RANK() OVER (PARTITION BY parent_cd, metric_key ORDER BY value)
    END * 100 AS mscore
  FROM joined
),
field AS (
  SELECT adm_cd, parent_cd, category, AVG(mscore) AS field_score, COUNT(*) AS metric_count
  FROM norm
  GROUP BY adm_cd, parent_cd, category
)
SELECT
  adm_cd,
  parent_cd,
  category,
  ROUND(field_score::numeric, 2) AS field_score,
  metric_count,
  RANK() OVER (PARTITION BY parent_cd, category ORDER BY field_score DESC) AS rank_in_sigungu,
  COUNT(*) OVER (PARTITION BY parent_cd, category) AS sigungu_count
FROM field;

CREATE UNIQUE INDEX neighborhood_field_scores_v1_pk
  ON public.neighborhood_field_scores_v1 (adm_cd, category);
CREATE INDEX neighborhood_field_scores_v1_parent
  ON public.neighborhood_field_scores_v1 (parent_cd, category);

-- refresh 함수에 분야 MV도 포함
CREATE OR REPLACE FUNCTION app_private.refresh_neighborhood_scores_impl()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, app_private
AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY public.neighborhood_scores_v1;
  REFRESH MATERIALIZED VIEW CONCURRENTLY public.neighborhood_field_scores_v1;
END;
$$;

GRANT SELECT ON public.neighborhood_field_scores_v1 TO anon, authenticated;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_readonly') THEN
    GRANT SELECT ON public.neighborhood_field_scores_v1 TO app_readonly;
  END IF;
END;
$$;
