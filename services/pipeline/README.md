# Public Officer Map Pipeline

Phase 1 pipeline modules:

- `crawler`: Seoul OpenGov list/detail crawler.
- `extractor`: HTML expense table extraction.
- `normalizer`: LLM-first normalizer with a deterministic test fallback.
- `entity`: Kakao Local resolver with natural-key fallback.
- `loader`: Neon Postgres direct SQL upsert loader.

Run the Seoul City Hall source:

```bash
uv run --project services/pipeline public-officer-pipeline run-seoul-city \
  --since 2026-04-24 \
  --limit-pages 3
```

Seed the v1 Seoul agency master:

```bash
uv run --project services/pipeline public-officer-pipeline seed-agencies
```

Run another Seoul OpenGov-backed agency from the master:

```bash
uv run --project services/pipeline public-officer-pipeline run-opengov-agency 서울시의회 \
  --since 2026-04-24 \
  --limit-pages 2
```

Refresh derived grades and agency stats after loading:

```bash
uv run --project services/pipeline public-officer-pipeline refresh-views
```

The production path requires `ANTHROPIC_API_KEY`, `KAKAO_REST_KEY`,
and `DATABASE_URL`. R2 upload additionally requires `R2_ACCOUNT_ID`,
`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, and `R2_BUCKET`.
