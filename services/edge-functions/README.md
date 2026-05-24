Supabase CLI deploys Edge Functions from `supabase/functions/`.

The production function sources live there so `supabase functions serve` and
`supabase functions deploy` work without extra path configuration. This folder
is kept as the architecture-level boundary referenced by `docs/RUNBOOK.md`.
