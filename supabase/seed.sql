INSERT INTO public.agencies (
  id,
  name,
  short_name,
  gov_tier,
  branch,
  jurisdiction_type,
  parent_region,
  sub_region,
  homepage,
  source_pattern
) VALUES (
  '00000000-0000-0000-0000-000000000001',
  '서울특별시청',
  '서울시청',
  'regional',
  'admin',
  'special_city',
  '서울특별시',
  NULL,
  'https://opengov.seoul.go.kr/expense/list',
  '{"adapter":"seoul_opengov","searchKeyword":"서울시본청"}'::jsonb
)
ON CONFLICT (gov_tier, branch, parent_region, sub_region) DO UPDATE
SET
  name = EXCLUDED.name,
  short_name = EXCLUDED.short_name,
  homepage = EXCLUDED.homepage,
  source_pattern = EXCLUDED.source_pattern;
