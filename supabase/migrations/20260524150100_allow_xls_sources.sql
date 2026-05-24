ALTER TABLE public.sources
  DROP CONSTRAINT IF EXISTS sources_file_kind_check;

ALTER TABLE public.sources
  ADD CONSTRAINT sources_file_kind_check
  CHECK (file_kind IN ('html', 'pdf', 'hwp', 'hwpx', 'xls', 'xlsx'));
