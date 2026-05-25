# plan8b.md — R2 Source Storage Adapter

## Execution Snapshot

- **Status**: Observed as implemented in the current worktree; final verification/checkpoint still required.
- **Resume point**: Confirm R2 storage adapter behavior and dry-run/missing-env paths, then mark complete in `STATUS.md`.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Implement the Cloudflare R2 raw-source preservation decision from ADR-010 and PIPELINE.md. After this plan, non-dry-run pipeline loads should have a real `sources.storage_path` for every fetched source artifact unless an explicit operator flag allows a local-only run.

## Prerequisites

- `plan8.md` is complete.
- R2 credentials may be absent locally; tests must use fake storage and must not require network.

## Read First

- `docs/adr/ADR-010-database-stack-migration.md`
- `docs/PIPELINE.md` fetcher section
- `docs/DATA_MODEL.md` `sources` section
- `services/pipeline/src/public_officer_pipeline/artifact.py`
- `services/pipeline/src/public_officer_pipeline/cli.py`
- `services/pipeline/src/public_officer_pipeline/loader/postgres.py`

## Files To Touch

Primary:

- `services/pipeline/src/public_officer_pipeline/storage/__init__.py` (new)
- `services/pipeline/src/public_officer_pipeline/storage/r2.py` (new)
- `services/pipeline/src/public_officer_pipeline/pipeline` files if plan12 already exists, otherwise `cli.py`
- `services/pipeline/src/public_officer_pipeline/loader/postgres.py`
- `services/pipeline/pyproject.toml`
- `services/pipeline/tests/test_storage_r2.py` (new)
- `services/pipeline/tests/test_*` pipeline/CLI tests touched by storage wiring
- `docs/PIPELINE.md`
- `docs/DATA_MODEL.md`

Do not modify crawler parsing or entity resolution in this plan.

## Dependency Decision

Use `boto3` as the S3-compatible client for Cloudflare R2:

```toml
"boto3>=1.34"
```

Do not hand-roll AWS Signature v4 with `httpx`.

## Target Interface

Create `public_officer_pipeline.storage.r2`:

```python
class SourceStorageError(RuntimeError): ...

class SourceStorage(Protocol):
    def put_artifact(self, artifact: SourceArtifact) -> str: ...

class R2SourceStorage:
    @classmethod
    def from_env(cls) -> "R2SourceStorage": ...
    def put_artifact(self, artifact: SourceArtifact) -> str: ...

class NullSourceStorage:
    def put_artifact(self, artifact: SourceArtifact) -> str | None: ...
```

Path format:

```text
r2://officer-map-raw/{agency_id}/{yyyy-mm}/{hash_sha256}.{file_kind}
```

The object key stored in R2 excludes the `r2://bucket/` prefix:

```text
{agency_id}/{yyyy-mm}/{hash_sha256}.{file_kind}
```

## Environment Variables

`R2SourceStorage.from_env()` requires:

```text
R2_ACCOUNT_ID
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY
R2_BUCKET
```

Endpoint:

```text
https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com
```

## Implementation Steps

1. Add the storage package and fake/null storage implementations.
2. Upload `artifact.content_bytes` for binary files; upload `artifact.html.encode("utf-8")` for HTML/text artifacts.
3. Set object metadata:
   - `agency_id`
   - `source_url`
   - `source_title`
   - `published_at` when present
   - `hash_sha256`
4. Wire storage into the pipeline:
   - If plan12 is complete, `PipelineRunner` calls storage after fetch and before load.
   - If plan12 is not complete, `cli._run_crawler` calls storage after `fetch_post` and passes the returned `storage_path` into `PostgresLoader.load`.
5. Add CLI flag:
   ```text
   --allow-missing-r2
   ```
   This flag may use `NullSourceStorage` and leave `storage_path=None`; without it, missing R2 env vars are a `PipelineConfigError` for non-dry-run runs.
6. Dry runs must not upload to R2 unless an explicit future flag says otherwise.
7. Update docs to state that production loads require non-null `storage_path`.

## Tests

Add tests:

- R2 key/path generation matches the exact format above.
- HTML artifact uploads UTF-8 bytes.
- Binary artifact uploads raw bytes.
- Missing required R2 env raises `PipelineConfigError` unless `--allow-missing-r2` / `NullSourceStorage` is used.
- Loader receives the storage path returned by storage wiring.
- Dry-run does not call storage.

Run:

```bash
npm run test:pipeline
rg -n "storage_path=None|allow-missing-r2|R2_" services/pipeline docs/PIPELINE.md docs/DATA_MODEL.md
```

## Acceptance Criteria

- Production pipeline loads cannot silently skip raw-source preservation.
- `sources.storage_path` uses the ADR-010 R2 path format.
- Storage is tested with fake clients and does not require network in CI.

## STOP Conditions

- If adding `boto3` causes dependency or lockfile problems, stop and report before choosing another SDK.
- If R2 env vars are not configured in deployment, code may merge but production crawl/deploy is blocked until env is added.
- If a source artifact has neither `content_bytes` nor `html`, stop and report the source; do not upload an empty object.
