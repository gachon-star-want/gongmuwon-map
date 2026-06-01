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

Seed the v1 Seoul agency master into staging:

```bash
uv run --project services/pipeline public-officer-pipeline seed-agencies
```

Seed the full P1-P4 nationwide agency master after the source registry gate is approved
(2,200 agencies as of 2026-06-01):

```bash
uv run --project services/pipeline public-officer-pipeline seed-agencies --scope nationwide
```

Inspect source verification state without crawling or writing to the database:

```bash
uv run --project services/pipeline public-officer-pipeline source-registry --scope nationwide
```

Run another Seoul OpenGov-backed agency from the master:

```bash
uv run --project services/pipeline public-officer-pipeline run-opengov-agency 서울시의회 \
  --since 2026-04-24 \
  --limit-pages 2
```

DB write commands default to staging and require `DATABASE_URL_STAGING` or
`STAGING_DATABASE_URL`.
Production writes require `--write-target production`, `--confirm-production-write`,
`--allow-production-write`, and `--production-gate-report` from a passing
staging verification run. Use `--dry-run` for Gate C validation without DB
writes.

```bash
uv run --project services/pipeline public-officer-pipeline run-agencies \
  --scope capital-area \
  --since 2026-04-24 \
  --limit-pages 2 \
  --max-posts 2 \
  --concurrency 6 \
  --max-attempts 5 \
  --agency-timeout-seconds 180 \
  --dry-run
```

Batch runs emit a single JSON object suitable for verification artifacts. Each
agency result includes `attempt_count`, `attempts[]`, `failure_reason`, parsed
and normalized counts, Kakao match counts, loaded row counts, and timeout stage
diagnostics when a wall-clock guard fires.
Use `--agency-timeout-seconds` on broad batches so one slow agency cannot block
the whole verification artifact.

Refresh derived grades and agency stats after loading into staging:

```bash
uv run --project services/pipeline public-officer-pipeline refresh-views
```

The production path requires `ANTHROPIC_API_KEY`, `KAKAO_REST_KEY`,
`DATABASE_URL`, and explicit production write flags. R2 upload additionally
requires runtime `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`,
and `R2_BUCKET`. For staging writes, `R2_STAGING_ACCOUNT_ID`,
`R2_STAGING_ACCESS_KEY_ID`, `R2_STAGING_SECRET_ACCESS_KEY`, and
`R2_STAGING_BUCKET` are also accepted. In GitHub Actions staging runs, those
staging secrets are mapped into runtime `R2_*` names.
