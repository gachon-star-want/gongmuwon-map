# plan8.md — Source Artifact Module

## Execution Snapshot

- **Status**: Observed as implemented in the current worktree; final verification/checkpoint still required.
- **Resume point**: Confirm source artifact hashing/provenance behavior, then mark complete in `STATUS.md`.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Introduce a Source Artifact Module between crawler discovery and extraction. Today crawler Adapters fetch content, hash bytes or HTML, timestamp the result, infer file shape, and create `PostDetail`. R2 storage is planned through `storage_path`, but no Module owns artifact identity or provenance.

## Read First

- `docs/PIPELINE.md` fetcher/extractor/loader sections
- `docs/v2/001_capital_area_expansion/03_BACKFILL_AND_PIPELINE_PLAN.md`
- `services/pipeline/src/public_officer_pipeline/models.py`
- `services/pipeline/src/public_officer_pipeline/crawler/*.py`
- `services/pipeline/src/public_officer_pipeline/loader/postgres.py`
- `services/pipeline/tests/test_gncouncil_crawler.py`
- `services/pipeline/tests/test_gangnam_crawler.py`

## Files To Touch

Primary:

- `services/pipeline/src/public_officer_pipeline/artifact.py` (new)
- `services/pipeline/src/public_officer_pipeline/models.py`
- `services/pipeline/src/public_officer_pipeline/crawler/*.py`
- `services/pipeline/src/public_officer_pipeline/cli.py`
- crawler tests

Do not implement R2 upload in this plan. `plan8b.md` owns the storage Adapter and is required before `LoadBatch.storage_path` becomes a non-null production invariant.

## Target Module Interface

```python
class SourceArtifact(BaseModel):
    agency_id: UUID
    url: str
    title: str
    published_at: date | None
    department_name: str | None
    file_kind: str
    html: str = ""
    content_bytes: bytes | None = None
    fetched_at: datetime
    hash_sha256: str
    storage_path: str | None = None

def artifact_from_response(ref: PostRef, response: Any, *, fallback_file_kind: str | None = None) -> SourceArtifact:
    ...

def post_detail_from_artifact(artifact: SourceArtifact) -> PostDetail:
    ...
```

Keep `PostDetail` temporarily for compatibility with extractors. `SourceArtifact` is the deeper Module; `PostDetail` can later be folded into it.

## Implementation Decisions

- Hash policy:
  - binary content: hash raw bytes
  - HTML/text content: hash UTF-8 encoded text actually passed to extractor
- Timestamp policy:
  - one `datetime.now(timezone.utc)` inside artifact creation
- File kind policy:
  - prefer `PostRef.file_kind`
  - allow Adapter-specific override from response headers only when current code already does so
- R2:
  - leave `storage_path=None` in this plan only
  - expose enough artifact metadata for `plan8b.md` to upload without recomputing hashes or timestamps

## Implementation Steps

1. Add `artifact.py` and tests for hashing/timestamps/file kind.
2. Update crawler `fetch_post` methods to delegate hash/timestamp construction to artifact helpers.
3. Keep crawler list parsing unchanged.
4. Update CLI extractor entrypoint only if it benefits from `SourceArtifact`; otherwise convert artifact back to `PostDetail`.
5. Ensure `PostgresLoader.load(... storage_path=...)` still receives the same value as before.

## Tests

Add tests:

- same HTML content yields same hash.
- same binary content yields same hash.
- artifact preserves `agency_id`, `url`, title, published date, department, and file kind from `PostRef`.
- Gangnam response header override still detects xlsx/xls.

Run:

```bash
npm run test:pipeline
```

## Acceptance Criteria

- Hashing and fetch timestamp logic are not duplicated in crawler Adapters.
- Artifact metadata is consistent across HTML and binary sources.
- Crawler Adapters focus on discovery and download, not provenance policy.

## STOP Conditions

- If tests rely on exact `fetched_at` values, introduce injectable clock in artifact helpers instead of weakening assertions.
- If R2 upload is requested during this plan, stop and split it into a storage Adapter plan.
