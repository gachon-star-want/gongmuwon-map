ALTER TABLE public.agencies
  ADD COLUMN IF NOT EXISTS gov_tier text,
  ADD COLUMN IF NOT EXISTS branch text,
  ADD COLUMN IF NOT EXISTS jurisdiction_type text,
  ADD COLUMN IF NOT EXISTS expansion_phase text;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'agencies'
      AND column_name = 'kind'
  ) THEN
    UPDATE public.agencies
    SET
      gov_tier = COALESCE(
        gov_tier,
        CASE
          WHEN kind IN ('city_hall', 'city_council') THEN 'regional'
          WHEN kind IN ('gu_office', 'gu_council') THEN 'basic'
          ELSE 'basic'
        END
      ),
      branch = COALESCE(
        branch,
        CASE
          WHEN kind IN ('city_council', 'gu_council') THEN 'council'
          ELSE 'admin'
        END
      ),
      jurisdiction_type = COALESCE(
        jurisdiction_type,
        CASE
          WHEN kind IN ('city_hall', 'city_council') THEN 'special_city'
          WHEN kind IN ('gu_office', 'gu_council') THEN 'autonomous_gu'
          ELSE 'autonomous_gu'
        END
      ),
      expansion_phase = COALESCE(expansion_phase, 'p1');
  ELSE
    UPDATE public.agencies
    SET
      gov_tier = COALESCE(gov_tier, 'basic'),
      branch = COALESCE(branch, 'admin'),
      jurisdiction_type = COALESCE(jurisdiction_type, 'autonomous_gu'),
      expansion_phase = COALESCE(expansion_phase, 'p1');
  END IF;
END;
$$;

ALTER TABLE public.agencies
  ALTER COLUMN gov_tier SET NOT NULL,
  ALTER COLUMN gov_tier SET DEFAULT 'basic',
  ALTER COLUMN branch SET NOT NULL,
  ALTER COLUMN branch SET DEFAULT 'admin',
  ALTER COLUMN jurisdiction_type SET NOT NULL,
  ALTER COLUMN jurisdiction_type SET DEFAULT 'autonomous_gu',
  ALTER COLUMN expansion_phase SET NOT NULL,
  ALTER COLUMN expansion_phase SET DEFAULT 'p1';

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'agencies'
      AND column_name = 'kind'
  ) THEN
    ALTER TABLE public.agencies
      ALTER COLUMN kind DROP NOT NULL;
  END IF;
END;
$$;

ALTER TABLE public.agencies
  DROP CONSTRAINT IF EXISTS agencies_gov_tier_check;

ALTER TABLE public.agencies
  ADD CONSTRAINT agencies_gov_tier_check
  CHECK (gov_tier IN ('regional', 'basic', 'national', 'constitutional', 'public', 'local_public'));

ALTER TABLE public.agencies
  DROP CONSTRAINT IF EXISTS agencies_branch_check;

ALTER TABLE public.agencies
  ADD CONSTRAINT agencies_branch_check
  CHECK (branch IN ('admin', 'council', 'constitutional', 'public'));

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
      'gun',
      'central_administrative_agency',
      'constitutional_institution',
      'independent_state_agency',
      'public_institution',
      'local_public_institution'
    )
  );

ALTER TABLE public.agencies
  DROP CONSTRAINT IF EXISTS agencies_expansion_phase_check;

ALTER TABLE public.agencies
  ADD CONSTRAINT agencies_expansion_phase_check
  CHECK (expansion_phase IN ('p1', 'p2', 'p3', 'p4'));

ALTER TABLE public.agencies
  DROP CONSTRAINT IF EXISTS agencies_kind_parent_region_sub_region_short_name_key;

ALTER TABLE public.agencies
  DROP CONSTRAINT IF EXISTS agencies_kind_parent_region_sub_region_key;

ALTER TABLE public.agencies
  DROP CONSTRAINT IF EXISTS agencies_gov_tier_branch_parent_region_sub_region_key;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'agencies_taxonomy_region_short_name_key'
      AND conrelid = 'public.agencies'::regclass
  ) THEN
    ALTER TABLE public.agencies
      ADD CONSTRAINT agencies_taxonomy_region_short_name_key
      UNIQUE NULLS NOT DISTINCT (gov_tier, branch, parent_region, sub_region, short_name);
  END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS agencies_tier_region
  ON public.agencies (gov_tier, branch, parent_region, sub_region);

DROP VIEW IF EXISTS public.agencies_public;

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

GRANT SELECT ON public.agencies_public TO anon, authenticated;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_readonly') THEN
    GRANT SELECT ON public.agencies_public TO app_readonly;
  END IF;
END;
$$;
