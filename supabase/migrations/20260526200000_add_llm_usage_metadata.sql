ALTER TABLE public.llm_usage
  ADD COLUMN IF NOT EXISTS thinking_tokens integer,
  ADD COLUMN IF NOT EXISTS task_id text,
  ADD COLUMN IF NOT EXISTS status text,
  ADD COLUMN IF NOT EXISTS error_code text;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint c
    WHERE c.conname = 'llm_usage_status_check'
      AND c.conrelid = 'public.llm_usage'::regclass
  ) THEN
    ALTER TABLE public.llm_usage
      ADD CONSTRAINT llm_usage_status_check
      CHECK (status IN ('success', 'fallback', 'error', 'skipped_budget') OR status IS NULL);
  END IF;
END $$;

