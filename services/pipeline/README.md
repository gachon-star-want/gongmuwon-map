# Public Officer Map Pipeline

Phase 1 pipeline modules:

- `crawler`: Seoul OpenGov list/detail crawler.
- `extractor`: HTML expense table extraction.
- `normalizer`: LLM-first normalizer with a deterministic test fallback.
- `entity`: Kakao Local resolver with natural-key fallback.
- `loader`: Supabase PostgREST upsert loader.

Run the Seoul City Hall source:

```bash
uv run --project services/pipeline public-officer-pipeline run-seoul-city \
  --since 2026-04-24 \
  --limit-pages 3
```

The production path requires `ANTHROPIC_API_KEY`, `KAKAO_REST_KEY`,
`SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY`.
