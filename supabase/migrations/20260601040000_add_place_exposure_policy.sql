ALTER TABLE public.places
  ADD COLUMN IF NOT EXISTS valid_place boolean NOT NULL DEFAULT true,
  ADD COLUMN IF NOT EXISTS is_restaurant_like boolean NOT NULL DEFAULT true,
  ADD COLUMN IF NOT EXISTS is_chain boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS is_large_chain boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS chain_brand text,
  ADD COLUMN IF NOT EXISTS chain_scale text;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'places_chain_scale_check'
      AND conrelid = 'public.places'::regclass
  ) THEN
    ALTER TABLE public.places
      ADD CONSTRAINT places_chain_scale_check
      CHECK (chain_scale IS NULL OR chain_scale IN ('대형전국체인', '지역체인'));
  END IF;
END;
$$;

UPDATE public.places
SET valid_place = false,
    updated_at = now()
WHERE regexp_replace(lower(coalesce(name, '')), '[\s./_()（）-]+', '', 'g')
  IN ('unknown', 'none', 'na', '정보없음', '미상', '해당없음', '없음', '장소없음', '불명');

WITH chain_candidates AS (
  SELECT
    id,
    CASE
      WHEN name ILIKE '%스타벅스%' OR name ILIKE '%starbucks%' THEN '스타벅스'
      WHEN name ILIKE '%투썸%' OR name ILIKE '%twosome%' THEN '투썸플레이스'
      WHEN name ILIKE '%메가커피%' OR name ILIKE '%메가mgc커피%' OR name ILIKE '%mega coffee%' THEN '메가커피'
      WHEN name ILIKE '%컴포즈%' OR name ILIKE '%compose coffee%' THEN '컴포즈커피'
      WHEN name ILIKE '%파리바게뜨%' OR name ILIKE '%파리바게트%' OR name ILIKE '%paris baguette%' THEN '파리바게뜨'
      WHEN name ILIKE '%맥도날드%' OR name ILIKE '%mcdonald%' THEN '맥도날드'
      WHEN name ILIKE '%버거킹%' OR name ILIKE '%burger king%' THEN '버거킹'
      WHEN name ILIKE '%롯데리아%' OR name ILIKE '%lotteria%' THEN '롯데리아'
      WHEN name ILIKE '%써브웨이%' OR name ILIKE '%서브웨이%' OR name ILIKE '%subway%' THEN '써브웨이'
      WHEN name ILIKE '%이디야%' OR name ILIKE '%ediya%' THEN '이디야커피'
      WHEN name ILIKE '%빽다방%' THEN '빽다방'
      WHEN name ILIKE '%커피빈%' OR name ILIKE '%coffee bean%' THEN '커피빈'
      WHEN name ILIKE '%할리스%' OR name ILIKE '%hollys%' THEN '할리스'
      WHEN name ILIKE '%배스킨라빈스%' OR name ILIKE '%베스킨라빈스%' OR name ILIKE '%baskin%' THEN '배스킨라빈스'
      WHEN name ILIKE '%던킨%' OR name ILIKE '%dunkin%' THEN '던킨'
      WHEN name ILIKE '%KFC%' THEN 'KFC'
      WHEN name ILIKE '%맘스터치%' OR name ILIKE '%momstouch%' THEN '맘스터치'
      ELSE NULL
    END AS chain_brand
  FROM public.places
)
UPDATE public.places p
SET is_chain = true,
    is_large_chain = true,
    chain_brand = c.chain_brand,
    chain_scale = '대형전국체인',
    updated_at = now()
FROM chain_candidates c
WHERE p.id = c.id
  AND c.chain_brand IS NOT NULL;

DROP VIEW IF EXISTS public.places_public;
DROP VIEW IF EXISTS public.place_visits_public;
DROP VIEW IF EXISTS public.agencies_public;
DROP MATERIALIZED VIEW IF EXISTS public.place_grade_v1;
DROP MATERIALIZED VIEW IF EXISTS public.agency_stats_v1;

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
    ELSE a.gov_tier
  END AS gov_tier_label,
  a.branch,
  CASE a.branch
    WHEN 'admin' THEN '집행기관'
    WHEN 'council' THEN '의회'
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
    ELSE a.jurisdiction_type
  END AS jurisdiction_type_label,
  a.parent_region,
  a.sub_region,
  a.homepage,
  COALESCE(s.visit_count, 0) AS visit_count,
  COALESCE(s.place_count, 0) AS place_count,
  s.last_visit_at
FROM public.agencies a
LEFT JOIN public.agency_stats_v1 s ON s.agency_id = a.id;

GRANT SELECT ON public.places_public TO anon, authenticated;
GRANT SELECT ON public.place_visits_public TO anon, authenticated;
GRANT SELECT ON public.agencies_public TO anon, authenticated;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_readonly') THEN
    GRANT SELECT ON public.places_public TO app_readonly;
    GRANT SELECT ON public.place_visits_public TO app_readonly;
    GRANT SELECT ON public.agencies_public TO app_readonly;
  END IF;
END;
$$;
