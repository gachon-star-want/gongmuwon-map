# plan6.md — Place Resolution Policy Module

## Execution Snapshot

- **Status**: Observed as implemented in the current worktree; final verification/checkpoint still required.
- **Resume point**: Confirm place-resolution policy tests and ADR-003 fallback behavior, then mark complete in `STATUS.md`.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Deepen place resolution into one policy Module. Current `KakaoResolver` mixes HTTP calls, cache, query generation, ranking, fallback identity, and `road_address_part`. It also diverges from ADR-003: no ±300m validation, no geohash7 fallback, no 7-day cache TTL, and Seoul-only region parsing.

## Read First

- `docs/adr/ADR-003-entity-resolution.md`
- `docs/PIPELINE.md` entity/geocoder sections
- `docs/v2/001_capital_area_expansion/04_DATA_QUALITY_PLAN.md`
- `services/pipeline/src/public_officer_pipeline/entity/resolver.py`
- `services/pipeline/tests/test_resolver.py`

## Files To Touch

Primary:

- `services/pipeline/src/public_officer_pipeline/entity/resolver.py`
- `services/pipeline/src/public_officer_pipeline/entity/policy.py` (new)
- `services/pipeline/src/public_officer_pipeline/entity/geohash.py` (new if no dependency is added)
- `services/pipeline/tests/test_resolver.py`
- `docs/DATA_MODEL.md`

Do not change loader SQL or existing place IDs in this plan unless the repo is confirmed pre-production.

## Target Module Interface

Create `entity/policy.py`:

```python
class PlaceResolutionPolicy:
    def candidate_queries(self, place: PlaceRaw) -> list[str]: ...
    def choose_best_kakao_document(self, place: PlaceRaw, documents: list[dict]) -> dict | None: ...
    def validate_candidate(self, place: PlaceRaw, document: dict) -> bool: ...
    def from_kakao_document(self, place: PlaceRaw, document: dict) -> ResolvedPlace: ...
    def fallback(self, place: PlaceRaw) -> ResolvedPlace: ...

def road_address_part(address: str | None) -> str | None: ...
def natural_key(name: str, address: str | None, latitude: float | None = None, longitude: float | None = None) -> str: ...
```

`KakaoResolver` becomes an Adapter that wires HTTP and cache to this policy.

## Policy Decisions

- Matching:
  - Prefer Kakao documents with `category_group_code == "FD6"`.
  - If `place.address_hint` exists, call Kakao address search before validating keyword candidates. Use the address-search coordinates as the source coordinate for ADR-003 validation.
  - If source and candidate coordinates are both available, reject candidates whose haversine distance is greater than 300m.
  - If coordinates cannot be derived, fall back to address string consistency using `road_address_part` and normalized address tokens.
- Cache:
  - Store `created_at` or `expires_at` in SQLite cache.
  - Default TTL: 7 days.
  - Expired cache entries are ignored and refreshed.
- Region parsing:
  - Seoul: `서울 중구`
  - Gyeonggi: `경기 수원시`, `경기 연천군`
  - Incheon: `인천 중구`, `인천 강화군`
- Fallback natural key:
  - If coordinates exist from address search or source data, use normalized name + geohash7.
  - If coordinates do not exist, use normalized name + normalized address hint.
  - If this changes current key behavior and production data exists, stop and require a migration plan.

## Implementation Steps

1. Extract pure functions from `resolver.py` into `policy.py`.
2. Add a small no-dependency geohash7 helper if no geohash library exists.
3. Update `KakaoResolver.resolve` to:
   - check cache with TTL
   - call Kakao address search for `address_hint` when needed to derive validation coordinates
   - call Kakao keyword/address Adapters
   - delegate selection/fallback to `PlaceResolutionPolicy`
4. Keep `allow_unmatched_fallback` behavior.
5. Update exports in `entity/__init__.py` if needed.
6. Update docs if fallback key semantics change.

## Tests

Add tests:

- `road_address_part("서울특별시 중구 서소문로 120") == "서울 중구"`
- `road_address_part("경기도 수원시 팔달구 ...") == "경기 수원시"`
- `road_address_part("인천광역시 강화군 ...") == "인천 강화군"`
- cache hit before TTL returns cached value.
- expired cache refreshes.
- fallback key is stable for same name/address.
- category ranking prefers food document.

Run:

```bash
npm run test:pipeline
```

## Acceptance Criteria

- `KakaoResolver` is an Adapter; resolution policy is testable without HTTP.
- Region partition extraction supports 수도권.
- Cache TTL and fallback identity are explicit.
- ADR-003 gaps are corrected or documented as impossible with current data.

## STOP Conditions

- If production contains existing fallback natural keys, do not change `natural_key` format without an ADR/migration.
- If adding geohash requires a new dependency, stop and decide whether to implement a no-dependency helper instead.
