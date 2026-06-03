DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN;
  END IF;
END;
$$;

CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS cube WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS earthdistance WITH SCHEMA extensions;

CREATE SCHEMA IF NOT EXISTS app_private;

CREATE TABLE public.agencies (
  id uuid PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
  name text NOT NULL,
  short_name text NOT NULL,
  gov_tier text NOT NULL CHECK (gov_tier IN ('regional', 'basic', 'national', 'constitutional', 'public', 'local_public')),
  branch text NOT NULL CHECK (branch IN ('admin', 'council', 'constitutional', 'public')),
  jurisdiction_type text NOT NULL CHECK (jurisdiction_type IN ('special_city', 'metro_city', 'province', 'special_self_governing_city', 'special_self_governing_province', 'autonomous_gu', 'si', 'gun', 'central_administrative_agency', 'constitutional_institution', 'independent_state_agency', 'public_institution', 'local_public_institution')),
  expansion_phase text NOT NULL DEFAULT 'p1' CHECK (expansion_phase IN ('p1', 'p2', 'p3', 'p4')),
  parent_region text NOT NULL,
  sub_region text,
  homepage text,
  source_pattern jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE NULLS NOT DISTINCT (gov_tier, branch, parent_region, sub_region, short_name)
);

CREATE INDEX agencies_tier_region ON public.agencies (gov_tier, branch, parent_region, sub_region);

CREATE TABLE public.sources (
  id uuid PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
  agency_id uuid NOT NULL REFERENCES public.agencies(id) ON DELETE RESTRICT,
  url text NOT NULL,
  title text,
  published_at date,
  file_kind text CHECK (file_kind IN ('html', 'pdf', 'hwp', 'hwpx', 'xls', 'xlsx', 'zip')),
  storage_path text,
  fetched_at timestamptz NOT NULL DEFAULT now(),
  hash_sha256 text NOT NULL,
  UNIQUE (agency_id, hash_sha256)
);

CREATE INDEX sources_agency_published ON public.sources (agency_id, published_at DESC);

CREATE TABLE public.places (
  id uuid PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
  kakao_place_id text UNIQUE,
  natural_key text UNIQUE NOT NULL,
  name text NOT NULL,
  road_address text,
  jibun_address text,
  road_address_part text,
  latitude double precision,
  longitude double precision,
  category text,
  phone text,
  valid_place boolean NOT NULL DEFAULT true,
  is_restaurant_like boolean NOT NULL DEFAULT true,
  is_chain boolean NOT NULL DEFAULT false,
  is_large_chain boolean NOT NULL DEFAULT false,
  chain_brand text,
  chain_scale text CHECK (chain_scale IS NULL OR chain_scale IN ('대형전국체인', '지역체인')),
  is_closed boolean NOT NULL DEFAULT false,
  closure_report_count integer NOT NULL DEFAULT 0,
  closed_at timestamptz,
  reopened_at timestamptz,
  hidden_at timestamptz,
  hidden_reason text,
  deleted_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK ((latitude IS NULL AND longitude IS NULL) OR (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180))
);

CREATE INDEX places_kakao ON public.places (kakao_place_id);
CREATE INDEX places_geo ON public.places USING gist (extensions.ll_to_earth(latitude, longitude));
CREATE INDEX places_active ON public.places (id) WHERE hidden_at IS NULL AND deleted_at IS NULL;

CREATE TABLE public.place_visits (
  id uuid PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
  place_id uuid NOT NULL REFERENCES public.places(id) ON DELETE RESTRICT,
  agency_id uuid NOT NULL REFERENCES public.agencies(id) ON DELETE RESTRICT,
  source_id uuid NOT NULL REFERENCES public.sources(id) ON DELETE RESTRICT,
  visit_date date NOT NULL,
  amount integer NOT NULL CHECK (amount >= 0),
  party_size integer CHECK (party_size IS NULL OR party_size > 0),
  purpose text,
  department_name text,
  rank_label text,
  representative text,
  payment_method text,
  expense_category text,
  raw_excerpt text,
  extracted_at timestamptz NOT NULL DEFAULT now(),
  extractor_model text NOT NULL,
  extractor_confidence numeric(3,2) CHECK (extractor_confidence IS NULL OR extractor_confidence BETWEEN 0 AND 1),
  UNIQUE (agency_id, visit_date, place_id, amount, department_name)
);

CREATE INDEX visits_place_date ON public.place_visits (place_id, visit_date DESC);
CREATE INDEX visits_agency_date ON public.place_visits (agency_id, visit_date DESC);
CREATE INDEX visits_date ON public.place_visits (visit_date DESC);

CREATE TABLE public.place_closure_reports (
  id uuid PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
  place_id uuid NOT NULL REFERENCES public.places(id) ON DELETE CASCADE,
  reporter_fp text NOT NULL,
  note text,
  resolved_at timestamptz,
  resolution text CHECK (resolution IS NULL OR resolution IN ('confirmed_closed', 'rejected', 'reopened')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (place_id, reporter_fp)
);

CREATE TABLE public.place_takedown_requests (
  id uuid PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
  place_id uuid NOT NULL REFERENCES public.places(id) ON DELETE CASCADE,
  reporter_email text,
  reason text NOT NULL,
  applied_at timestamptz,
  reviewed_at timestamptz,
  reviewer_note text,
  resolution text CHECK (resolution IS NULL OR resolution IN ('permanent_delete', 'restore', 'mask_more')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.llm_usage (
  id uuid PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
  task_type text NOT NULL,
  provider text NOT NULL,
  model text NOT NULL,
  input_tokens integer,
  output_tokens integer,
  estimated_cost_usd numeric(10,4),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.extraction_failures (
  id uuid PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
  agency_id uuid REFERENCES public.agencies(id) ON DELETE SET NULL,
  source_url text,
  source_title text,
  error_code text NOT NULL,
  error_message text NOT NULL,
  payload jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE MATERIALIZED VIEW public.place_grade_v1 AS
WITH window_visits AS (
  SELECT v.*
  FROM public.place_visits v
  JOIN public.places p ON p.id = v.place_id
  WHERE v.visit_date >= (current_date - interval '12 months')
    AND p.hidden_at IS NULL
    AND p.deleted_at IS NULL
    AND p.valid_place IS TRUE
    AND p.is_restaurant_like IS TRUE
    AND p.is_large_chain IS FALSE
),
agg AS (
  SELECT
    place_id,
    COUNT(*)::integer AS visit_count_12m,
    COUNT(DISTINCT department_name)::integer AS unique_department_count_12m,
    COUNT(DISTINCT agency_id)::integer AS unique_agency_count_12m,
    MAX(visit_date) AS last_visit_at,
    MIN(visit_date) AS first_visit_at
  FROM window_visits
  GROUP BY place_id
),
scored AS (
  SELECT
    a.*,
    (a.visit_count_12m * LOG(a.unique_department_count_12m + 1))::numeric(10,4) AS score,
    p.road_address_part,
    COUNT(*) OVER (PARTITION BY p.road_address_part) AS region_place_count
  FROM agg a
  JOIN public.places p ON p.id = a.place_id
),
ranked AS (
  SELECT
    *,
    CASE
      WHEN region_place_count >= 30 THEN PERCENT_RANK() OVER (PARTITION BY road_address_part ORDER BY score)
      ELSE PERCENT_RANK() OVER (ORDER BY score)
    END AS pct
  FROM scored
)
SELECT
  place_id,
  score,
  visit_count_12m,
  unique_department_count_12m,
  unique_agency_count_12m,
  last_visit_at,
  first_visit_at,
  CASE
    WHEN visit_count_12m <= 2 AND first_visit_at >= current_date - interval '3 months' THEN '✦'
    WHEN pct >= 0.90 THEN '★★★'
    WHEN pct >= 0.70 THEN '★★'
    WHEN pct >= 0.40 THEN '★'
    ELSE NULL
  END AS grade
FROM ranked;

CREATE UNIQUE INDEX place_grade_v1_pk ON public.place_grade_v1 (place_id);

CREATE MATERIALIZED VIEW public.agency_stats_v1 AS
SELECT
  a.id AS agency_id,
  COUNT(v.id) FILTER (WHERE p.id IS NOT NULL)::integer AS visit_count,
  COUNT(DISTINCT v.place_id) FILTER (WHERE p.id IS NOT NULL)::integer AS place_count,
  MAX(v.visit_date) FILTER (WHERE p.id IS NOT NULL) AS last_visit_at
FROM public.agencies a
LEFT JOIN public.place_visits v ON v.agency_id = a.id
LEFT JOIN public.places p
  ON p.id = v.place_id
  AND p.hidden_at IS NULL
  AND p.deleted_at IS NULL
  AND p.valid_place IS TRUE
  AND p.is_restaurant_like IS TRUE
  AND p.is_large_chain IS FALSE
GROUP BY a.id;

CREATE UNIQUE INDEX agency_stats_v1_pk ON public.agency_stats_v1 (agency_id);

CREATE VIEW public.places_public WITH (security_barrier = true) AS
SELECT
  p.id,
  p.name,
  p.road_address,
  p.road_address_part,
  p.latitude,
  p.longitude,
  p.category,
  p.valid_place,
  p.is_restaurant_like,
  p.is_chain,
  p.is_large_chain,
  p.chain_brand,
  p.chain_scale,
  p.is_closed,
  p.closure_report_count,
  COALESCE(g.score, 0) AS score,
  COALESCE(g.grade, '✦') AS grade,
  g.last_visit_at,
  g.visit_count_12m,
  g.unique_department_count_12m
FROM public.places p
LEFT JOIN public.place_grade_v1 g ON g.place_id = p.id
WHERE p.hidden_at IS NULL
  AND p.deleted_at IS NULL
  AND p.valid_place IS TRUE
  AND p.is_restaurant_like IS TRUE
  AND p.is_large_chain IS FALSE;

CREATE VIEW public.place_visits_public WITH (security_barrier = true) AS
SELECT
  v.id,
  v.place_id,
  v.agency_id,
  v.visit_date,
  v.amount,
  v.party_size,
  v.department_name,
  v.rank_label,
  v.representative,
  v.purpose,
  s.url AS source_url,
  s.title AS source_title
FROM public.place_visits v
JOIN public.sources s ON s.id = v.source_id
JOIN public.places p ON p.id = v.place_id
WHERE p.hidden_at IS NULL
  AND p.deleted_at IS NULL
  AND p.valid_place IS TRUE
  AND p.is_restaurant_like IS TRUE
  AND p.is_large_chain IS FALSE;

CREATE VIEW public.agencies_public WITH (security_barrier = true) AS
SELECT
  a.id,
  a.name,
  a.short_name,
  a.gov_tier,
  CASE a.gov_tier
    WHEN 'regional' THEN '광역자치단체'
    WHEN 'basic' THEN '기초자치단체'
    WHEN 'national' THEN '국가기관'
    WHEN 'constitutional' THEN '헌법기관'
    WHEN 'public' THEN '공공기관'
    WHEN 'local_public' THEN '지방공공기관'
    ELSE a.gov_tier
  END AS gov_tier_label,
  a.branch,
  CASE a.branch
    WHEN 'admin' THEN '집행기관'
    WHEN 'council' THEN '의회'
    WHEN 'constitutional' THEN '헌법기관'
    WHEN 'public' THEN '공공기관'
    ELSE a.branch
  END AS branch_label,
  a.jurisdiction_type,
  CASE a.jurisdiction_type
    WHEN 'special_city' THEN '특별시'
    WHEN 'metro_city' THEN '광역시'
    WHEN 'province' THEN '도'
    WHEN 'special_self_governing_city' THEN '특별자치시'
    WHEN 'special_self_governing_province' THEN '특별자치도'
    WHEN 'autonomous_gu' THEN '자치구'
    WHEN 'si' THEN '시'
    WHEN 'gun' THEN '군'
    WHEN 'central_administrative_agency' THEN '중앙행정기관'
    WHEN 'constitutional_institution' THEN '헌법기관'
    WHEN 'independent_state_agency' THEN '독립국가기관'
    WHEN 'public_institution' THEN '지정 공공기관'
    WHEN 'local_public_institution' THEN '지방공공기관'
    ELSE a.jurisdiction_type
  END AS jurisdiction_type_label,
  a.expansion_phase,
  CASE a.expansion_phase
    WHEN 'p1' THEN 'P1 지방자치단체·의회'
    WHEN 'p2' THEN 'P2 중앙행정기관·독립기관'
    WHEN 'p3' THEN 'P3 지정 공공기관'
    WHEN 'p4' THEN 'P4 지방공공기관'
    ELSE a.expansion_phase
  END AS expansion_phase_label,
  a.parent_region,
  a.sub_region,
  a.homepage,
  COALESCE(s.visit_count, 0) AS visit_count,
  COALESCE(s.place_count, 0) AS place_count,
  s.last_visit_at
FROM public.agencies a
LEFT JOIN public.agency_stats_v1 s ON s.agency_id = a.id;

CREATE OR REPLACE FUNCTION app_private.report_closure_impl(p_place_id uuid, p_fp text, p_note text DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, app_private
AS $$
DECLARE
  v_count integer;
BEGIN
  INSERT INTO public.place_closure_reports (place_id, reporter_fp, note)
  VALUES (p_place_id, p_fp, p_note)
  ON CONFLICT (place_id, reporter_fp) DO NOTHING;

  SELECT COUNT(*) INTO v_count
  FROM public.place_closure_reports
  WHERE place_id = p_place_id;

  UPDATE public.places
  SET
    closure_report_count = v_count,
    is_closed = CASE WHEN v_count >= 3 THEN true ELSE is_closed END,
    closed_at = CASE WHEN v_count >= 3 AND closed_at IS NULL THEN now() ELSE closed_at END,
    updated_at = now()
  WHERE id = p_place_id;

  RETURN jsonb_build_object('place_id', p_place_id, 'closure_report_count', v_count, 'is_closed', v_count >= 3);
END;
$$;

CREATE OR REPLACE FUNCTION public.report_closure(place_id uuid, fp text, note text DEFAULT NULL)
RETURNS jsonb
LANGUAGE sql
SECURITY INVOKER
SET search_path = public, app_private
AS $$
  SELECT app_private.report_closure_impl(place_id, fp, note);
$$;

CREATE OR REPLACE FUNCTION app_private.request_takedown_impl(p_place_id uuid, p_reason text, p_email text DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, app_private
AS $$
DECLARE
  v_request_id uuid;
BEGIN
  INSERT INTO public.place_takedown_requests (place_id, reason, reporter_email, applied_at)
  VALUES (p_place_id, p_reason, p_email, now())
  RETURNING id INTO v_request_id;

  UPDATE public.places
  SET hidden_at = now(),
      hidden_reason = 'notice_takedown',
      updated_at = now()
  WHERE id = p_place_id;

  RETURN jsonb_build_object('request_id', v_request_id, 'place_id', p_place_id, 'hidden', true);
END;
$$;

CREATE OR REPLACE FUNCTION public.request_takedown(place_id uuid, reason text, email text DEFAULT NULL)
RETURNS jsonb
LANGUAGE sql
SECURITY INVOKER
SET search_path = public, app_private
AS $$
  SELECT app_private.request_takedown_impl(place_id, reason, email);
$$;

CREATE OR REPLACE FUNCTION app_private.recompute_grades_impl()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, app_private
AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY public.place_grade_v1;
  REFRESH MATERIALIZED VIEW CONCURRENTLY public.agency_stats_v1;
END;
$$;

CREATE OR REPLACE FUNCTION public.recompute_grades()
RETURNS void
LANGUAGE sql
SECURITY INVOKER
SET search_path = public, app_private
AS $$
  SELECT app_private.recompute_grades_impl();
$$;

ALTER TABLE public.agencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.places ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.place_visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.place_closure_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.place_takedown_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.llm_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_failures ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.agencies, public.sources, public.places, public.place_visits,
  public.place_closure_reports, public.place_takedown_requests, public.llm_usage,
  public.extraction_failures FROM anon, authenticated;

GRANT SELECT ON public.places_public TO anon, authenticated;
GRANT SELECT ON public.place_visits_public TO anon, authenticated;
GRANT SELECT ON public.agencies_public TO anon, authenticated;
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT USAGE ON SCHEMA app_private TO service_role;
GRANT EXECUTE ON FUNCTION public.report_closure(uuid, text, text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.request_takedown(uuid, text, text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.recompute_grades() TO service_role;
GRANT EXECUTE ON FUNCTION app_private.recompute_grades_impl() TO service_role;

REVOKE USAGE ON SCHEMA app_private FROM anon, authenticated;
REVOKE EXECUTE ON FUNCTION app_private.report_closure_impl(uuid, text, text) FROM anon, authenticated;
REVOKE EXECUTE ON FUNCTION app_private.request_takedown_impl(uuid, text, text) FROM anon, authenticated;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_readonly') THEN
    GRANT USAGE ON SCHEMA public TO app_readonly;
    GRANT SELECT ON public.places_public TO app_readonly;
    GRANT SELECT ON public.place_visits_public TO app_readonly;
    GRANT SELECT ON public.agencies_public TO app_readonly;
  END IF;
END;
$$;
