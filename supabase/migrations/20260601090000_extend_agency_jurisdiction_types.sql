ALTER TABLE public.agencies
  DROP CONSTRAINT IF EXISTS agencies_jurisdiction_type_check;

ALTER TABLE public.agencies
  ADD CONSTRAINT agencies_jurisdiction_type_check
  CHECK (
    jurisdiction_type IN (
      'special_city',
      'metro_city',
      'province',
      'special_self_governing_city',
      'special_self_governing_province',
      'autonomous_gu',
      'si',
      'gun'
    )
  );

CREATE OR REPLACE VIEW public.agencies_public WITH (security_barrier = true) AS
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
