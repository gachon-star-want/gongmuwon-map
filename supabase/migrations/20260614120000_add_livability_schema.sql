-- 거주적합도('동네') 스키마: 행정구역 트리 + 지표 + 가구원수 가중치 + 사전계산 점수 MV
-- ADR-015(점수 공식) / ADR-016(공간 데이터) / ADR-017(통합·정체성)
-- 지역코드는 SGIS=KOSIS 공통 통계청 adm_cd(시도2/시군구5/읍면동8).

-- ── 행정구역 트리 ───────────────────────────────────────────────
CREATE TABLE public.adm_regions (
  adm_cd      text PRIMARY KEY,
  level       text NOT NULL CHECK (level IN ('sido', 'sigungu', 'emd')),
  parent_cd   text REFERENCES public.adm_regions(adm_cd),
  name        text NOT NULL,
  full_name   text NOT NULL,
  center_lat  double precision,
  center_lng  double precision,
  bbox        jsonb,
  ref_year    integer NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX adm_regions_parent ON public.adm_regions(parent_cd);
CREATE INDEX adm_regions_level ON public.adm_regions(level);

-- 법정동↔행정동 안분 매핑(Phase 3 실거래가용으로 미리 생성)
CREATE TABLE public.adm_code_map (
  bjd_code  text NOT NULL,
  hjd_code  text NOT NULL REFERENCES public.adm_regions(adm_cd),
  weight    numeric NOT NULL DEFAULT 1.0,
  PRIMARY KEY (bjd_code, hjd_code)
);

-- 읍면동 경계 폴리곤(WGS84로 변환 저장 → 카카오맵 직접 사용)
CREATE TABLE public.region_boundaries (
  adm_cd    text PRIMARY KEY REFERENCES public.adm_regions(adm_cd),
  geojson   jsonb NOT NULL,
  ref_year  integer NOT NULL
);

-- 수집 감사/버전
CREATE TABLE public.ingest_runs (
  id          uuid PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
  source_id   text NOT NULL,
  scope       text,
  ref_period  text,
  row_count   integer,
  status      text NOT NULL DEFAULT 'success',
  started_at  timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  artifact    jsonb
);
CREATE INDEX ingest_runs_source ON public.ingest_runs(source_id, started_at DESC);

-- 지표 메타 카탈로그(방향성·환산법을 데이터로 관리; ADR-015/016)
CREATE TABLE public.metric_catalog (
  metric_key        text PRIMARY KEY,
  category          text NOT NULL,          -- convenience/safety/housing/education/vitality/environment/welfare
  display_name      text NOT NULL,
  unit              text,
  direction         smallint NOT NULL CHECK (direction IN (-1, 1)),  -- 1=높을수록 좋음
  source_id         text NOT NULL,
  native_resolution text NOT NULL DEFAULT 'emd',                     -- emd/sigungu/station/bjd
  allocation        text NOT NULL DEFAULT 'direct',                  -- direct/pop_weighted/idw/broadcast
  refresh_cadence   text NOT NULL DEFAULT 'yearly',
  source_notice     text NOT NULL
);

-- 읍면동 × 지표 raw 값(long-format). household_size: NULL=일반지표, 1~6=가구원수별(표시용)
CREATE TABLE public.neighborhood_metrics (
  adm_cd          text NOT NULL REFERENCES public.adm_regions(adm_cd),
  metric_key      text NOT NULL REFERENCES public.metric_catalog(metric_key),
  household_size  smallint NOT NULL DEFAULT 0,  -- 0=가구원수 무관(일반지표), 1~6=가구원수별(표시용)
  value           numeric,
  ref_period      text NOT NULL,
  source_resolution text NOT NULL DEFAULT 'emd',
  as_of_year      integer,
  imputed         boolean NOT NULL DEFAULT false,
  ingest_run_id   uuid REFERENCES public.ingest_runs(id),
  PRIMARY KEY (adm_cd, metric_key, household_size, ref_period)
);
CREATE INDEX neighborhood_metrics_metric ON public.neighborhood_metrics(metric_key, ref_period);

-- 가구원수별 분야(category) 가중치 프로파일(versioned; ADR-015 v1)
CREATE TABLE public.household_weights (
  profile_version integer NOT NULL,
  household_size  smallint NOT NULL,        -- 1,2,3,4(=4인 이상)
  category        text NOT NULL,
  weight          numeric NOT NULL,
  PRIMARY KEY (profile_version, household_size, category)
);

-- ── 사전계산 점수 MV: 시군구 내 percentile → 분야평균 → 가구원수 가중합 → 랭킹 ──
CREATE MATERIALIZED VIEW public.neighborhood_scores_v1 AS
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
  SELECT adm_cd, parent_cd, category, AVG(mscore) AS field_score
  FROM norm
  GROUP BY adm_cd, parent_cd, category
),
composite AS (
  SELECT
    f.adm_cd, f.parent_cd, hw.profile_version, hw.household_size,
    SUM(hw.weight * f.field_score) / NULLIF(SUM(hw.weight), 0) AS score,
    COUNT(*) AS field_count
  FROM field f
  JOIN public.household_weights hw ON hw.category = f.category
  GROUP BY f.adm_cd, f.parent_cd, hw.profile_version, hw.household_size
)
SELECT
  adm_cd,
  parent_cd,
  profile_version,
  household_size,
  ROUND(score::numeric, 2) AS score,
  field_count,
  RANK() OVER (PARTITION BY parent_cd, profile_version, household_size ORDER BY score DESC) AS rank_in_sigungu,
  COUNT(*) OVER (PARTITION BY parent_cd, profile_version, household_size) AS sigungu_emd_count
FROM composite;

CREATE UNIQUE INDEX neighborhood_scores_v1_pk
  ON public.neighborhood_scores_v1 (adm_cd, household_size, profile_version);
CREATE INDEX neighborhood_scores_v1_parent
  ON public.neighborhood_scores_v1 (parent_cd, household_size, profile_version);

-- ── refresh 함수(recompute_grades 패턴) ─────────────────────────
CREATE OR REPLACE FUNCTION app_private.refresh_neighborhood_scores_impl()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, app_private
AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY public.neighborhood_scores_v1;
END;
$$;

CREATE OR REPLACE FUNCTION public.refresh_neighborhood_scores()
RETURNS void
LANGUAGE sql
SECURITY INVOKER
SET search_path = public, app_private
AS $$
  SELECT app_private.refresh_neighborhood_scores_impl();
$$;

-- ── 가구원수 가중치 v1 시드(ADR-015) ────────────────────────────
INSERT INTO public.household_weights (profile_version, household_size, category, weight) VALUES
  (1,1,'convenience',28),(1,1,'safety',20),(1,1,'housing',15),(1,1,'education',5),(1,1,'vitality',17),(1,1,'environment',10),(1,1,'welfare',5),
  (1,2,'convenience',24),(1,2,'safety',15),(1,2,'housing',22),(1,2,'education',8),(1,2,'vitality',13),(1,2,'environment',10),(1,2,'welfare',8),
  (1,3,'convenience',16),(1,3,'safety',18),(1,3,'housing',18),(1,3,'education',22),(1,3,'vitality',8),(1,3,'environment',14),(1,3,'welfare',4),
  (1,4,'convenience',14),(1,4,'safety',18),(1,4,'housing',16),(1,4,'education',24),(1,4,'vitality',7),(1,4,'environment',15),(1,4,'welfare',6);

-- ── MVP 지표 카탈로그 시드(SGIS population + 통계주제도) ─────────
INSERT INTO public.metric_catalog (metric_key, category, display_name, unit, direction, source_id, native_resolution, allocation, refresh_cadence, source_notice) VALUES
  ('pop_density','vitality','인구밀도','명/㎢',1,'sgis','emd','direct','yearly','출처: 국가데이터처 SGIS 통계지리정보'),
  ('avg_age','vitality','평균나이','세',-1,'sgis','emd','direct','yearly','출처: 국가데이터처 SGIS 통계지리정보'),
  ('aging_index','vitality','노령화지수','명/백명',-1,'sgis','emd','direct','yearly','출처: 국가데이터처 SGIS 통계지리정보'),
  ('biz_per_1k','convenience','인구 천명당 사업체수','개',1,'sgis','emd','direct','yearly','출처: 국가데이터처 SGIS 통계주제도'),
  ('childcare_access','education','보육시설 접근성(1개당 어린이)','명',-1,'sgis','emd','direct','yearly','출처: 국가데이터처 SGIS 통계주제도'),
  ('health_access','welfare','보건시설 접근성(1개당 노인)','명',-1,'sgis','emd','direct','yearly','출처: 국가데이터처 SGIS 통계주제도'),
  ('culture_access','welfare','문화시설 접근성(1개당 인구)','명',-1,'sgis','emd','direct','yearly','출처: 국가데이터처 SGIS 통계주제도'),
  ('solo_household_ratio','vitality','1인가구 비율','%',1,'kosis','emd','direct','yearly','출처: 통계청 KOSIS 인구주택총조사'),
  ('household_count','demographics','가구원수별 가구수','가구',1,'kosis','emd','direct','yearly','출처: 통계청 KOSIS 인구주택총조사');

-- ── 권한(거주 데이터는 공개 통계) ───────────────────────────────
GRANT SELECT ON public.adm_regions, public.region_boundaries, public.metric_catalog,
  public.neighborhood_metrics, public.household_weights, public.neighborhood_scores_v1
  TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.refresh_neighborhood_scores() TO service_role;
GRANT EXECUTE ON FUNCTION app_private.refresh_neighborhood_scores_impl() TO service_role;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_readonly') THEN
    GRANT SELECT ON public.adm_regions, public.region_boundaries, public.metric_catalog,
      public.neighborhood_metrics, public.household_weights, public.neighborhood_scores_v1
      TO app_readonly;
  END IF;
END;
$$;
