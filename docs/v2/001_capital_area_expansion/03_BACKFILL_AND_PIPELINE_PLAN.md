# 03 — Backfill & Pipeline Plan

- **Status**: Planning (documentation only)
- **Date**: 2026-05-25

## 1. Purpose

Describe how the existing v1 pipeline is applied to the 86 new capital-area agencies: data windows, batch ordering, extraction strategy across formats, failure/retry, raw preservation in R2, loading into Neon, and the mandatory dry-run/staging gate **before** any production write.

> Seoul is already wired and live ([02_SOURCE_REGISTRY_PLAN.md](02_SOURCE_REGISTRY_PLAN.md) §2); this plan does **not** re-crawl Seoul. It applies the same pipeline to the 86 new agencies only.

## 2. Data window policy — unchanged from v1 **[FACT]**

Carried over verbatim from [AGENTS.md](../../../AGENTS.md) / [docs/PRD.md](../../PRD.md):

- **Rolling 12 months** → used for grade computation.
- **24-month backfill** → retained for future analysis, **not** fed into the grade.
- **Daily crawl** → once per day per source.

For each new agency, the target is: backfill the last 24 months where the board makes them available, and keep the last 12 months feeding the grade. Where a board only exposes a shorter history, that is recorded in the registry `notes` and the agency simply has a shorter backfill (no fabrication).

## 3. Pipeline reuse — same stages as v1 **[FACT]**

The v1 pipeline ([docs/PIPELINE.md](../../PIPELINE.md)) is reused unchanged in shape:

```
Crawler → Fetcher → Extractor → LLM Normalizer → Entity Resolver → Geocoder → Loader
```

- **All-LLM general extraction** stays the strategy ([ADR-002](../../adr/ADR-002-llm-extraction.md)); new agencies need no per-site hand-coded parser. The generic LLM adapter infers list selectors/paging and stores them in `agencies.source_pattern`.
- **Multi-provider routing** (ADR-009) stays: Gemini/Haiku for bulk tables, Claude vision for scanned PDFs, Sonnet for name normalization and masking verification.
- **Idempotency** stays: same source URL + same SHA-256 hash ⇒ skip. Re-runs are safe.

## 4. Batch ordering (proposed)

Rationale: start with the smallest, most uniform region to validate the end-to-end flow on new jurisdictions before taking on the largest one.

| Order | Batch | Agencies | Why this order |
|---|---|---|---|
| 1 | **Incheon** | 22 | Smallest new region. Validates province/metro `kind` handling, name-collision handling (중구/동구/서구 vs Seoul), and the dry-run→staging→prod gate end-to-end on a manageable set. |
| 2 | **Gyeonggi sample (5–10 시·군)** | ~10–20 | A representative slice of Gyeonggi (mix of large 특례시, mid city, and a 군) to surface format diversity before committing to all 64. |
| 3 | **Gyeonggi full** | remainder of 64 | Roll out the rest once the sample proves the patterns. |
| 4 | **Capital-area unified grade recompute** | all | Recompute `place_grade_v1` so every 시·군·구 is its own percentile partition. Seoul partitions are unaffected; new partitions appear. |

> This ordering mirrors the rollout batches in [05_DB_ROLLOUT_PLAN.md](05_DB_ROLLOUT_PLAN.md) §"Batched rollout" so that "crawl batch" and "DB promotion batch" stay aligned.

**[ASSUMPTION]** Each batch runs first as a dry-run against staging, is signed off on the quality gates ([04_DATA_QUALITY_PLAN.md](04_DATA_QUALITY_PLAN.md)), and only then is promoted. No batch writes to production before its dry-run passes.

## 5. Format handling (PDF / HWP / HWPX / XLSX / HTML)

Same extractor matrix as [docs/PIPELINE.md](../../PIPELINE.md) §3, reused as-is:

| Format | Primary | Fallback |
|---|---|---|
| HTML | `selectolax` table selectors | LLM on raw HTML |
| PDF (text-based) | `pdfplumber` table extraction | pdf→image + LLM vision |
| PDF (scanned image) | LLM vision directly | — |
| XLSX / XLS | `openpyxl` | LLM on CSV conversion |
| HWP | `hwp5txt` CLI → text | LibreOffice CLI → PDF → PDF pipe |
| HWPX | XML parse (`Contents/section0.xml`) | same as HWP fallback |

**[RISK / ASSUMPTION]** Gyeonggi/Incheon agencies are expected to lean more on **HWP/HWPX** and **scanned PDF** than Seoul's relatively HTML/XLSX-friendly portals. Specifically:

- HWP/HWPX coverage must be validated early (the Incheon batch is a good first probe). If `hwp5txt`/LibreOffice conversion fails on real samples, escalate to the LLM-vision-on-rendered-PDF path before scaling.
- Scanned PDFs route straight to Claude vision (per ADR-009). Track scanned-PDF share per agency in the registry `notes`.

No new extraction *capability* is assumed; if a format appears that the matrix cannot handle, that is a tracked blocker, not a silent skip.

## 6. Failure, retry, raw preservation, R2, Neon load

Reused from [docs/PIPELINE.md](../../PIPELINE.md) §"에러 처리 정책" and [docs/ARCHITECTURE.md](../../ARCHITECTURE.md):

1. **Crawl/site down**: 3 retries with exponential backoff; final failure deferred to next cycle; 24h continuous failure raises an alert.
2. **Raw preservation**: every fetched file is hashed (SHA-256) and uploaded to **Cloudflare R2** `officer-map-raw/{agency_short}/{yyyy-mm}/{hash}.{ext}`; a `sources` row records `storage_path`, `published_at`, `file_kind`, `hash_sha256`. Egress-free R2 is what makes shipping raw files to the LLM cheap.
3. **Parse failure**: original + error go to the extraction-failure queue for operator review; the row is not silently dropped.
4. **LLM failure**: 30s timeout, 3 retries, then escalate to the next model in the routing table; persistent failure → human queue.
5. **Kakao quota**: defer to next cycle; if no placeId, fall back to self natural_key (`normalize(name) + geohash7`).
6. **Neon load**: batches of ~500 rows via the connection pooler; transaction rollback + alert on failure. Natural key `(agency_id, visit_date, place_id, amount, department_name)` guarantees idempotent upsert.

## 7. Masking happens at load time — non-negotiable **[FACT]**

Per [docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) and [docs/PIPELINE.md](../../PIPELINE.md) §"마스킹 룰":

- Personal real names (except elected officials: 시장/도지사/시장·군수·구청장/광역·기초 의원) are removed **during normalization**, never stored in plaintext and masked later.
- A schema validator rejects any output where a 2–4 char Korean name leaks into a non-`representative` column.
- For Gyeonggi/Incheon the elected-official set expands to include **도지사 (governor)** and **시장·군수·구청장** and **광역의원/기초의원**; the masking prompt must enumerate these so the new regions are handled correctly. This is a prompt/config detail to confirm during the Incheon dry-run, and it must conform to [docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) (final authority). See [06_LEGAL_AND_RISK_PLAN.md](06_LEGAL_AND_RISK_PLAN.md).

## 8. Dry-run / staging gate (mandatory before production)

**No batch writes to the production database before passing this gate.**

Proposed staging mechanism (reusing existing stack — [ADR-010](../../adr/ADR-010-database-stack-migration.md)):

1. **Neon branch as staging.** Create a Neon branch (e.g. `staging-v2-incheon`) isolated from production. Neon branching is already a chosen capability; no new infra.
2. **Dry-run load** the batch into the staging branch only. Raw files still go to R2 (idempotent; shared), but `place_visits` rows land in staging.
3. **Run the quality gates** from [04_DATA_QUALITY_PLAN.md](04_DATA_QUALITY_PLAN.md) against the staging branch: parse success, masking SQL checks, placeId match rate, dedupe, grade distribution, regional sampling.
4. **Operator sign-off** on the gate results (recorded).
5. **Promotion** to production only after sign-off — see [05_DB_ROLLOUT_PLAN.md](05_DB_ROLLOUT_PLAN.md).

> The dry-run is also where the §6 `kind` enum question ([01_SCOPE.md](01_SCOPE.md) §6) gets exercised on real data; if the schema needs a new `kind` value, that surfaces here and blocks promotion until resolved (possibly via a new ADR).

## 9. What this stage does NOT do

- Does not run any crawler against a real Gyeonggi/Incheon site.
- Does not create the Neon staging branch.
- Does not call the LLM or load any row anywhere.
- It only specifies *how* those steps will run when later approved.
