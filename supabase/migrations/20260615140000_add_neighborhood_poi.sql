-- POI 근거(표시 전용) — 점수와 물리 분리 (ADR-019)
-- ⚠️ 경고: 이 테이블들은 점수 MV(neighborhood_scores_v1 / neighborhood_field_scores_v1)에서
--    절대 참조하지 않는다. 참조하면 "시설 많음=좋은 동네"로 점수가 오염된다(ADR-015/018).
--    CI 가드(.github)가 점수 MV SQL에 poi 참조가 들어오면 빌드를 실패시킨다.

CREATE TABLE IF NOT EXISTS public.poi_type_catalog (
  poi_type      text PRIMARY KEY,
  category      text NOT NULL CHECK (category IN ('convenience', 'education', 'welfare')),
  display_name  text NOT NULL,
  source_id     text NOT NULL,
  source_notice text NOT NULL,
  sort_order    int  NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS public.neighborhood_poi_counts (
  adm_cd         text NOT NULL REFERENCES public.adm_regions(adm_cd),
  poi_type       text NOT NULL REFERENCES public.poi_type_catalog(poi_type),
  distance_basis text NOT NULL CHECK (distance_basis IN ('pip', 'buffer_1km_straight')),
  ref_period     text NOT NULL,
  count          int  NOT NULL DEFAULT 0,
  source_id      text,
  ingest_run_id  uuid REFERENCES public.ingest_runs(id),
  updated_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (adm_cd, poi_type, distance_basis, ref_period)
);

CREATE INDEX IF NOT EXISTS idx_neighborhood_poi_counts_adm
  ON public.neighborhood_poi_counts (adm_cd);

COMMENT ON TABLE public.neighborhood_poi_counts IS
  'POI 근거(표시 전용). ADR-019: 점수 MV에서 참조 금지. count는 동 경계 내(pip) 또는 직선버퍼(buffer_1km_straight) 추정.';

-- 시드: POI 유형 카탈로그(분야별)
INSERT INTO public.poi_type_catalog (poi_type, category, display_name, source_id, source_notice, sort_order) VALUES
  ('elementary_school', 'education',   '초등학교',        'school_data',    '공공누리 제1유형 · 전국초중등학교위치 표준데이터(교육부)', 10),
  ('middle_school',     'education',   '중학교',          'school_data',    '공공누리 제1유형 · 전국초중등학교위치 표준데이터(교육부)', 11),
  ('high_school',       'education',   '고등학교',        'school_data',    '공공누리 제1유형 · 전국초중등학교위치 표준데이터(교육부)', 12),
  ('childcare',         'education',   '어린이집',        'childcare_data', '공공누리 제1유형 · 전국어린이집 표준데이터(보건복지부)',   13),
  ('hospital',          'welfare',     '병원',            'localdata',      '공공누리 제1유형 · 지방행정 인허가 데이터(행정안전부)',     20),
  ('clinic',            'welfare',     '의원',            'localdata',      '공공누리 제1유형 · 지방행정 인허가 데이터(행정안전부)',     21),
  ('pharmacy',          'welfare',     '약국',            'localdata',      '공공누리 제1유형 · 지방행정 인허가 데이터(행정안전부)',     22),
  ('large_store',       'convenience', '대형마트·백화점', 'localdata',      '공공누리 제1유형 · 지방행정 인허가 데이터(행정안전부)',     30),
  ('traditional_market','convenience', '전통시장',        'localdata',      '공공누리 제1유형 · 지방행정 인허가 데이터(행정안전부)',     31)
ON CONFLICT (poi_type) DO NOTHING;

GRANT SELECT ON public.poi_type_catalog, public.neighborhood_poi_counts TO anon, authenticated;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_readonly') THEN
    GRANT SELECT ON public.poi_type_catalog, public.neighborhood_poi_counts TO app_readonly;
  END IF;
END $$;
