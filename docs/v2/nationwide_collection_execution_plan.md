# 전국 업무추진비 데이터셋 수집 실행 계획

- 작성일: 2026-06-01
- 목표: 기존 DB 데이터셋의 구조와 품질을 기준으로 전국 단위 업무추진비 데이터를 처음부터 수집·정제·적재하고, 검증 리포트까지 산출한 뒤 서비스 주입 가능 상태를 만든다.
- 금지선: 명시 승인 전까지 production DB 쓰기, 배포, 원본 삭제, irreversible cleanup 금지.

## 사용자 합의 기준

- 전국 범위는 P1-P4 전체 2,200개 기관을 최종 목표로 둔다.
- “전국 수집 완료”는 단순 기관 마스터 등록이 아니라 `sources`, `places`, `place_visits`, R2 원본, 공개 뷰 집계까지 기존 DB와 같은 계약으로 재현되는 상태를 말한다.
- 현재 `pending`/`legal_hold` 기관은 수집 누락이 아니라 검증/법적 게이트 미통과 상태로 리포트에 남긴다. 공식 URL·공공누리·첨부 접근성 검증 전에는 우회 수집하지 않는다.
- 1차 산출물은 staging 검증 리포트다. 서비스 주입은 staging 리포트 통과 후 별도 승인 게이트로 진행한다.

## 기존 DB 실측 기준선

2026-06-01 read-only 조회 기준:

| 항목 | 값 |
|---|---:|
| `agencies` | 52 |
| `sources` | 227 |
| `places` | 5,018 |
| `place_visits` | 11,327 |
| 방문 있는 기관 | 51 |
| 방문 없는 기관 | 1 |
| 방문일 범위 | 2024-01-02 ~ 2026-05-22 |
| `sources` 파일 종류 | pdf 126, html 69, xlsx 20, xls 12 |
| Kakao placeId 매칭 | 3,555 / 5,018 |
| 좌표 보유 place | 3,780 / 5,018 |
| `representative` 저장 | 0 / 11,327 |
| 평균 extractor confidence | 0.82 |

운영 DB는 현재 `agencies.kind` 기반 공개 스키마다. 로컬 최신 코드와 마이그레이션은 `gov_tier`, `branch`, `jurisdiction_type`, `expansion_phase` 기반이므로, 전국 주입 전에 staging에서 스키마 승격 리허설이 필요하다.

## 전국 source registry 기준

| 그룹 | 전체 | verified_in_code | pending | legal_hold | invalid_source_pattern |
|---|---:|---:|---:|---:|---:|
| 전체 P1-P4 | 2,200 | 137 | 1,996 | 67 | 0 |
| P1 지방자치단체·의회 | 486 | 137 | 282 | 67 | 0 |
| P2 중앙행정기관·독립기관 | 60 | 0 | 60 | 0 | 0 |
| P3 지정 공공기관 | 342 | 0 | 342 | 0 | 0 |
| P4 지방공공기관 | 1,312 | 0 | 1,312 | 0 | 0 |

즉시 크롤 가능한 1차 실행 후보는 `verified_in_code` 137개뿐이다. `pending` 1,996개와 `legal_hold` 67개는 공식 출처 승격 작업의 대상이다.

## 실행 원칙

1. 기존 production 데이터는 기준선으로만 읽는다.
2. Neon staging branch를 production에서 복제한 뒤 모든 schema migration, seed, load, report를 staging에서 먼저 수행한다.
3. production load는 staging과 같은 코드·같은 source registry·같은 명령을 재실행하는 방식으로만 한다. staging 데이터를 production에 직접 복사하지 않는다.
4. R2는 staging/prod bucket을 분리하거나 최소한 staging prefix를 강제한다. raw 원본 혼재가 해결되기 전에는 production load를 금지한다.
5. `adapter_required`, `pending`, `legal_hold`는 크롤 대상에서 제외한다. 리포트에는 제외 사유와 다음 액션을 남긴다.

## Phase 0: Staging 격리

목표: 기존 DB와 동일한 데이터셋을 안전하게 재현할 빈 공간을 만든다.

현재 상태:

- Neon project `gongmuwon-map`에 staging branch `nationwide-staging-20260601`을 생성했다.
- branch id: `br-dawn-paper-aonnud0v`
- parent branch: `main`
- state: `ready`
- connection string은 리포트나 문서에 기록하지 않는다. `DATABASE_URL_STAGING`은 secret manager 또는 로컬 shell에서만 설정한다.

작업:

1. `DATABASE_URL_STAGING` 또는 `STAGING_DATABASE_URL`을 설정한다.
2. production service `DATABASE_URL`은 staging shell에서 제거하거나, production 명령에만 명시적으로 사용한다.
3. R2 staging bucket 또는 prefix를 확정한다.
4. baseline 리포트를 양쪽에서 생성한다.

명령:

```bash
npm run report:db-baseline -- --target=readonly --output=/private/tmp/nationwide-production-baseline.json
npm run report:db-baseline -- --target=staging --output=/private/tmp/nationwide-staging-before.json
```

통과 기준:

- staging baseline이 production baseline과 같은 row count/date window로 시작한다.
- staging 연결이 `BEGIN READ ONLY` baseline 리포트에서 성공한다.
- production URL이 staging 실행 shell에 노출되지 않는다.

## Phase 1: Schema 승격 리허설

목표: 운영 DB의 `kind` 기반 스키마를 최신 전국 스키마로 staging에서만 승격한다.

작업:

1. staging에 최신 migration을 적용한다.
2. `agencies_public`가 기존 API 계약을 깨지 않고 신규 taxonomy label을 함께 노출하는지 확인한다.
3. 기존 52개 agency가 동일 ID·동일 공개 응답을 유지하는지 확인한다.

기존 운영 DB에서 복제한 staging branch는 이미 초기 schema가 적용돼 있으므로 `20260523235106_initial.sql`을 재실행하지 않는다. live schema 승격은 forward migration 순서로만 실행한다.

명령:

```bash
for migration in \
  supabase/migrations/20260524150100_allow_xls_sources.sql \
  supabase/migrations/20260526200000_add_llm_usage_metadata.sql \
  supabase/migrations/20260601030000_migrate_live_agency_kind_to_taxonomy.sql \
  supabase/migrations/20260601040000_add_place_exposure_policy.sql \
  supabase/migrations/20260601090000_extend_agency_jurisdiction_types.sql \
  supabase/migrations/20260601103000_extend_agency_public_taxonomy_labels.sql
do
  uv --cache-dir /private/tmp/uv-cache run --project services/pipeline \
    public-officer-pipeline apply-schema --migration "$migration"
done
```

주의:

- `apply-schema`는 기본값으로 `DATABASE_URL_STAGING`을 사용한다.
- production에 `apply-schema`를 실행하려면 `--write-target production --confirm-production-write --allow-production-write`가 필요하며, 이 계획에서는 Phase 7 전까지 금지한다.

통과 기준:

- `agencies_public`는 기존 52개를 유지하면서 2,200개로 확장된다.
- `places_public`, `place_visits_public` 감소가 있으면 exposure-policy migration의 대형 체인·비식당·무효 장소 제외와 일치해야 한다.
- `/api/v1/*` public contract 테스트가 staging schema와 호환된다.
- 기존 52개 기관 ID가 유지된다.

## Phase 2: 전국 agency seed

목표: staging에 P1-P4 2,200개 기관 마스터를 넣되 기존 52개와 충돌하지 않게 한다.

명령:

```bash
uv --cache-dir /private/tmp/uv-cache run --project services/pipeline public-officer-pipeline source-registry --scope nationwide --format json --summary-only
uv --cache-dir /private/tmp/uv-cache run --project services/pipeline public-officer-pipeline seed-agencies --scope nationwide
```

통과 기준:

- staging `agencies_public` = 2,200.
- 기존 52개 agency ID 유지.
- `priority_group`/`expansion_phase`별 카운트가 source registry와 일치.
- `invalid_source_pattern` = 0.

## Phase 3: 전국 dry-run

목표: 전국 스코프를 처음부터 실행하되 DB/R2에 쓰지 않고, 실제 수집 가능한 기관과 제외 기관을 분리한다.

권장 1차 명령:

```bash
uv --cache-dir /private/tmp/uv-cache run --project services/pipeline public-officer-pipeline run-agencies \
  --scope nationwide \
  --since 2024-01-01 \
  --limit-pages 3 \
  --max-posts 10 \
  --dry-run \
  --quality-mode fail \
  --max-attempts 5 \
  --agency-timeout-seconds 180 \
  --concurrency 6
```

예상 결과:

- `verified_in_code` 기관만 crawler/extractor/normalizer/resolver까지 실행된다.
- `pending`/`legal_hold` 기관은 `adapter_required` 또는 보류 사유로 리포트된다.
- retry 가능한 실패는 기관별 `attempts[]`에 최대 5회까지 남고, 최종 `failure_reason`으로 집계된다.
- `--agency-timeout-seconds`는 기관 단위 전체 retry wall-clock을 제한해 장시간 미응답 사이트를 `timeout`으로 리포트한다.
- `legal_visibility`, 좌표 누락, confidence, storage path 요구 조건이 검증된다.

## Phase 4: Staging load

목표: dry-run 통과 기관만 staging DB와 R2 staging 저장소에 적재한다.

명령:

```bash
uv --cache-dir /private/tmp/uv-cache run --project services/pipeline public-officer-pipeline run-agencies \
  --scope nationwide \
  --since 2024-01-01 \
  --limit-pages 3 \
  --max-posts 10 \
  --write-target staging \
  --quality-mode fail \
  --max-attempts 5 \
  --agency-timeout-seconds 180 \
  --concurrency 6
```

통과 기준:

- `loaded_sources`, `loaded_places`, `loaded_visits`가 기관별 리포트에 기록된다.
- `storage_path` 누락 = 0.
- 마스킹 위반 = 0.
- 재실행 시 `sources`, `places`, `place_visits`의 순증이 0 또는 설명 가능한 신규 원문에 한정된다.

## Phase 5: 검증 리포트

리포트는 최소 다음 섹션을 가진다.

1. 기준선 비교
   - production read-only baseline
   - staging before migration
   - staging after migration/seed/load
2. source registry coverage
   - P1-P4별 total/verified/pending/legal_hold/invalid
   - legal_hold 이유 상위 분류
3. 수집 실행 결과
   - 기관별 attempt_count/max_attempts, attempts[], failure_reason.
   - 기관별 posts_seen/posts_fetched/parsed_rows/normalized_visits/places_seen/kakao_matched_places/loaded_*.
   - summary.failure_reasons로 source_not_found, legal_hold, auth_js_download, parser_missing, llm_extraction_failure, kakao_resolution, db_constraint, storage_failure를 집계한다.
4. 품질 게이트
   - 마스킹 위반 0 여부
   - `representative` 정책 위반 0 여부
   - 평균 confidence, low confidence 격리 건
   - 좌표 누락률
   - skipped_invalid_places
   - source storage path 누락
5. 공개 API 영향
   - `places_public`, `place_visits_public`, `agencies_public` row count
   - `place_grade_v1`, `agency_stats_v1` refresh 후 count
   - `npm run check:public-contracts`
6. 서비스 주입 판정
   - production 주입 가능 기관
   - pending 승격 필요 기관
   - legal_hold 유지 기관
   - production 금지 사유

생성 명령:

```bash
npm run report:nationwide-verification -- \
  --production-baseline=/private/tmp/nationwide-production-baseline.json \
  --staging-baseline-before=/private/tmp/nationwide-staging-before.json \
  --staging-baseline-after=/private/tmp/nationwide-staging-after.json \
  --source-registry=/private/tmp/nationwide-source-registry-summary.json \
  --dry-run=/private/tmp/nationwide-dry-run.json \
  --staging-load=/private/tmp/nationwide-staging-load.json \
  --public-contract=pass \
  --output=docs/v2/nationwide_verification_report.md
```

## 반복 수집 GitHub Actions 경로

`daily-crawl.yml`은 전국 반복 수집의 운영 진입점이다. 기존 Seoul-only production loop는 사용하지 않는다.

스케줄 실행:

- 매일 03:00 KST에 `mode=staging-load`, `scope=nationwide`로 실행한다.
- production service `DATABASE_URL`은 스케줄 job env에 주입하지 않는다.
- production 기준선은 `DATABASE_URL_READONLY`로만 읽는다.
- staging baseline before → staging schema/seed → nationwide dry-run → staging load → staging view refresh → staging baseline after 순서로 실행한다.
- dry-run과 staging load는 모두 `run-agencies --max-attempts 5 --agency-timeout-seconds 180`을 사용하고, 기관별 `attempts[]`, `attempt_count`, `failure_reason`을 JSON artifact로 남긴다.
- `source-registry`, baseline JSON, dry-run JSON, staging-load JSON, public contract status, verification report는 `nationwide-crawl-<run_id>` artifact로 업로드한다.

필수 GitHub Secrets:

| 용도 | Secret |
|---|---|
| production 기준선 읽기 | `DATABASE_URL_READONLY` |
| staging DB 쓰기 | `DATABASE_URL_STAGING` 또는 `STAGING_DATABASE_URL` |
| staging R2 원본 저장 | `R2_STAGING_ACCOUNT_ID`, `R2_STAGING_ACCESS_KEY_ID`, `R2_STAGING_SECRET_ACCESS_KEY`, `R2_STAGING_BUCKET` |
| 추출/정규화/지오코딩 | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `KAKAO_REST_KEY` |

수동 실행 모드:

| mode | 쓰기 대상 | 용도 |
|---|---|---|
| `dry-run` | 없음 | source registry와 전국 dry-run artifact만 확인 |
| `staging-load` | staging | 스케줄과 같은 staging-first 반복 수집 |
| production load | production | `daily-crawl.yml` 범위 밖. staging report 승인 뒤 별도 CLI/승인 흐름에서만 실행 |

production load는 `--write-target production --confirm-production-write --allow-production-write --production-gate-report <검증리포트>`를 모두 요구한다. 검증 리포트는 `서비스 주입 판정: production 주입 검토 가능` 상태여야 한다.

## Phase 6: Pending 승격 작업

`pending` 기관은 공식 업무추진비 URL 검증과 어댑터 구현이 선행되어야 한다.

승격 체크리스트:

- 기관 공식 홈페이지 확인.
- 업무추진비 원문 목록 URL 확인.
- URL host가 기관 홈페이지 host와 같거나 하위 도메인.
- 공공누리 제1유형 또는 동등한 자유이용 근거 확인.
- `fileKinds`, `pageParam`, `followDetail`, `extraListUrls`, JS download handler 기록.
- 1~2페이지 dry-run 성공.
- `verifiedAt`, `verifiedBy`, `homepage` 채움.
- `source-registry`에서 `verified_in_code`로 전환 확인.

## Phase 7: Service injection

production 주입은 다음 조건을 모두 만족할 때만 검토한다.

- staging load 리포트 통과.
- backup/PITR/rollback 기록 확보.
- production migration 계획 승인.
- R2 prod bucket/prefix 분리 확인.
- production load 명령에 대한 사용자 명시 승인.

production 명령은 staging에서 검증한 동일 명령을 `--write-target production --confirm-production-write --allow-production-write`로 재실행한다. 이 단계 전까지 production DB 쓰기와 배포는 금지다.

## 현재 다음 작업

1. GitHub Secrets에 `DATABASE_URL_STAGING` 또는 `STAGING_DATABASE_URL`과 `R2_STAGING_*` 값을 설정한다.
2. `daily-crawl.yml`을 `mode=staging-load`, `scope=nationwide`로 수동 실행해 스케줄과 같은 경로를 먼저 검증한다.
3. artifact의 `nationwide-verification-report.md`에서 staging before/after, dry-run, staging load, public contract를 확인한다.
4. 실패 기관은 `failure_reason`별로 source registry 승격, parser 보강, LLM/R2/Kakao 설정 보정 작업으로 분리한다.
5. production 주입은 staging report 통과와 별도 승인 전까지 실행하지 않는다.
