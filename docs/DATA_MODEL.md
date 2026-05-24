# DATA_MODEL — Supabase 스키마

## 설계 원칙

1. **모든 anon 읽기는 `*_public` 뷰로만**. 원본 테이블은 service role 전용.
2. **모든 anon 쓰기는 RPC 함수로만**. 직접 INSERT/UPDATE/DELETE 금지.
3. **소프트 삭제** (`hidden_at`, `deleted_at`) — 노티스앤테이크다운 복원 가능.
4. **자연키로 멱등성 보장** — 같은 데이터 여러 번 적재해도 중복 없음.
5. **개인 실명은 적재 단계에서 마스킹** — DB에 절대 평문 저장 금지.

## 테이블 일람

| 테이블 | 용도 | RLS |
|---|---|---|
| `agencies` | 기관(시청·구청·의회 등) 마스터 | service-only |
| `places` | 식당 마스터 | service-only |
| `place_visits` | 방문 트랜잭션 (1 row = 1 회식·간담회) | service-only |
| `place_closure_reports` | 폐업 신고 | service-only insert, anon insert via RPC |
| `place_takedown_requests` | 정보 삭제 요청 | service-only insert, anon insert via RPC |
| `place_grade_v1` (MAT VIEW) | 등급 계산 결과 | service-only |
| `places_public` (VIEW) | anon 노출 | anon read |
| `place_visits_public` (VIEW) | anon 노출 (마스킹된 부서·직급만) | anon read |
| `agencies_public` (VIEW) | anon 노출 | anon read |
| `agency_stats_v1` (MAT VIEW) | 기관별 통계 | anon read via view |
| `sources` | 원본 출처 (URL·파일·게시일) | service-only |

## SQL 스키마

### `agencies` — 기관 마스터

```sql
CREATE TABLE agencies (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name            text NOT NULL,              -- "서울특별시청", "강남구의회"
  short_name      text NOT NULL,              -- "서울시청", "강남구의회"
  kind            text NOT NULL,              -- 'city_hall' | 'city_council' | 'gu_office' | 'gu_council'
  parent_region   text NOT NULL,              -- '서울특별시'
  sub_region      text,                       -- '강남구' (시청·시의회는 NULL)
  homepage        text,
  source_pattern  jsonb,                      -- 크롤러 어댑터 힌트
  created_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (kind, parent_region, sub_region)
);

CREATE INDEX agencies_kind_region ON agencies (kind, parent_region, sub_region);
```

### `places` — 식당 마스터

```sql
CREATE TABLE places (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Entity Resolution 키
  kakao_place_id      text UNIQUE,            -- 카카오 로컬 매칭 성공 시
  natural_key         text UNIQUE NOT NULL,   -- 폴백 자연키 (normalized_name + geohash7)

  -- 표시 정보
  name                text NOT NULL,
  road_address        text,
  jibun_address       text,
  road_address_part   text,                   -- 시/구 부분만 (예: "서울 중구")
  latitude            double precision,
  longitude           double precision,
  category            text,                   -- 카카오 분류 (식당 > 한식 등)
  phone               text,

  -- 운영 상태
  is_closed           boolean NOT NULL DEFAULT false,
  closure_report_count integer NOT NULL DEFAULT 0,
  closed_at           timestamptz,
  reopened_at         timestamptz,

  -- 모더레이션
  hidden_at           timestamptz,            -- 노티스앤테이크다운 임시 차단
  hidden_reason       text,
  deleted_at          timestamptz,            -- 영구 삭제 (소프트)

  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX places_kakao ON places (kakao_place_id);
CREATE INDEX places_geo ON places USING gist (
  ll_to_earth(latitude, longitude)
);  -- earthdistance 익스텐션 또는 PostGIS
CREATE INDEX places_active ON places (id) WHERE hidden_at IS NULL AND deleted_at IS NULL;
```

### `place_visits` — 방문 트랜잭션

```sql
CREATE TABLE place_visits (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  place_id          uuid NOT NULL REFERENCES places(id) ON DELETE RESTRICT,
  agency_id         uuid NOT NULL REFERENCES agencies(id) ON DELETE RESTRICT,
  source_id         uuid NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,

  -- 원본에서 추출한 정형 데이터
  visit_date        date NOT NULL,
  amount            integer NOT NULL,          -- 원
  party_size        integer,                   -- 인원수 (NULL 가능)
  purpose           text,                      -- "정책 협의", "유관기관 간담회"
  department_name   text,                      -- "총무국 인사과" (마스킹된)
  rank_label        text,                      -- "국장" 또는 "5급 이하"
  representative    text,                      -- 선거직 실명 또는 NULL
  payment_method    text,                      -- "법인카드" 등
  expense_category  text,                      -- 비목

  -- 정규화 메타
  raw_excerpt       text,                      -- 원문에서 발췌한 1줄 (모더레이션·디버깅용)
  extracted_at      timestamptz NOT NULL DEFAULT now(),
  extractor_model   text NOT NULL,             -- "claude-haiku-4-5" 등
  extractor_confidence numeric(3,2),

  -- 자연키 (멱등성)
  UNIQUE (agency_id, visit_date, place_id, amount, department_name)
);

CREATE INDEX visits_place_date ON place_visits (place_id, visit_date DESC);
CREATE INDEX visits_agency_date ON place_visits (agency_id, visit_date DESC);
CREATE INDEX visits_date ON place_visits (visit_date DESC);
```

### `sources` — 원본 출처

```sql
CREATE TABLE sources (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id       uuid NOT NULL REFERENCES agencies(id) ON DELETE RESTRICT,
  url             text NOT NULL,
  title           text,
  published_at    date,
  file_kind       text,                       -- 'html' | 'pdf' | 'hwp' | 'xlsx'
  storage_path    text,                       -- raw-sources/{agency}/{yyyy-mm}/{hash}.pdf
  fetched_at      timestamptz NOT NULL DEFAULT now(),
  hash_sha256     text NOT NULL,
  UNIQUE (agency_id, hash_sha256)
);
```

### `place_closure_reports`, `place_takedown_requests` — 사용자 신고

```sql
CREATE TABLE place_closure_reports (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  place_id        uuid NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  reporter_fp     text NOT NULL,              -- 익명 fingerprint (브라우저 토큰)
  note            text,
  resolved_at     timestamptz,
  resolution      text,                       -- 'confirmed_closed' | 'rejected' | 'reopened'
  created_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (place_id, reporter_fp)              -- 같은 사람 중복 신고 차단
);

CREATE TABLE place_takedown_requests (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  place_id        uuid NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  reporter_email  text,
  reason          text NOT NULL,
  applied_at      timestamptz,                -- 임시 hide 적용 시각
  reviewed_at     timestamptz,
  reviewer_note   text,
  resolution      text,                       -- 'permanent_delete' | 'restore' | 'mask_more'
  created_at      timestamptz NOT NULL DEFAULT now()
);
-- v1.1: visit_id 컬럼 추가 예정 (visit 단위 takedown)
```

## 뷰 / 머티리얼라이즈드 뷰

### `places_public` — anon 노출

```sql
CREATE VIEW places_public AS
SELECT
  p.id,
  p.name,
  p.road_address,
  p.road_address_part,
  p.latitude,
  p.longitude,
  p.category,
  p.is_closed,
  p.closure_report_count,
  COALESCE(g.score, 0) AS score,
  COALESCE(g.grade, '✦') AS grade,
  g.last_visit_at,
  g.visit_count_12m,
  g.unique_department_count_12m
FROM places p
LEFT JOIN place_grade_v1 g ON g.place_id = p.id
WHERE p.hidden_at IS NULL AND p.deleted_at IS NULL;
```

### `place_grade_v1` — 등급 머티리얼라이즈드 뷰

```sql
CREATE MATERIALIZED VIEW place_grade_v1 AS
WITH window_visits AS (
  SELECT *
  FROM place_visits
  WHERE visit_date >= (current_date - interval '12 months')
),
agg AS (
  SELECT
    place_id,
    COUNT(*) AS visit_count_12m,
    COUNT(DISTINCT department_name) AS unique_department_count_12m,
    COUNT(DISTINCT agency_id) AS unique_agency_count_12m,
    MAX(visit_date) AS last_visit_at,
    MIN(visit_date) AS first_visit_at
  FROM window_visits
  GROUP BY place_id
),
scored AS (
  SELECT
    a.*,
    a.visit_count_12m * LOG(a.unique_department_count_12m + 1) AS score,
    p.road_address_part
  FROM agg a
  JOIN places p ON p.id = a.place_id
),
ranked AS (
  SELECT
    *,
    PERCENT_RANK() OVER (PARTITION BY road_address_part ORDER BY score) AS pct
  FROM scored
)
SELECT
  place_id,
  score,
  visit_count_12m,
  unique_department_count_12m,
  unique_agency_count_12m,
  last_visit_at,
  first_visit_at,
  CASE
    WHEN visit_count_12m <= 2 AND first_visit_at >= current_date - interval '3 months' THEN '✦'
    WHEN pct >= 0.90 THEN '★★★'
    WHEN pct >= 0.70 THEN '★★'
    WHEN pct >= 0.40 THEN '★'
    ELSE NULL
  END AS grade
FROM ranked;

CREATE UNIQUE INDEX place_grade_v1_pk ON place_grade_v1 (place_id);
```

`recompute-grades` Edge Function이 매일 03:30 KST에 `REFRESH MATERIALIZED VIEW CONCURRENTLY` 실행.

### `place_visits_public` — anon 노출 (마스킹 검증 후)

```sql
CREATE VIEW place_visits_public AS
SELECT
  v.id,
  v.place_id,
  v.agency_id,
  v.visit_date,
  v.amount,
  v.party_size,
  v.department_name,    -- 이미 마스킹된 값
  v.rank_label,
  v.representative,     -- 선거직만 NULL이 아님
  v.purpose,
  s.url AS source_url,
  s.title AS source_title
FROM place_visits v
JOIN sources s ON s.id = v.source_id
JOIN places p ON p.id = v.place_id
WHERE p.hidden_at IS NULL AND p.deleted_at IS NULL;
```

## RPC 함수 (anon 쓰기 진입점)

### `report_closure(place_id uuid, fp text, note text)`
- 같은 `(place_id, fp)` 중복 차단.
- 신고 누적 3건 이상이면 `places.is_closed = true`, `closed_at = now()` 자동 갱신.

### `request_takedown(place_id uuid, reason text, email text)`
- 즉시 `places.hidden_at = now()` 설정 (v1은 식당 단위 hide만 지원).
- 운영자에게 이메일 알림 (Edge Function이 Resend 호출).
- **v1.1**: visit 단위 hide를 위한 `place_visits.hidden_at` 컬럼 추가 + `visit_id` 인자 지원 예정.

### `mark_reopen(place_id uuid, fp text)`
- "다시 영업해요" 정정 신고. 임계값 별도(예: 누적 2건).

## RLS 정책 핵심

```sql
ALTER TABLE places ENABLE ROW LEVEL SECURITY;
ALTER TABLE place_visits ENABLE ROW LEVEL SECURITY;
-- 등 모든 테이블

-- anon은 직접 SELECT 금지
CREATE POLICY no_anon_select ON places FOR SELECT USING (false);

-- 뷰는 SECURITY DEFINER 또는 GRANT로 노출
GRANT SELECT ON places_public TO anon, authenticated;
GRANT SELECT ON place_visits_public TO anon, authenticated;
GRANT SELECT ON agencies_public TO anon, authenticated;

-- 쓰기는 RPC만
GRANT EXECUTE ON FUNCTION report_closure TO anon;
GRANT EXECUTE ON FUNCTION request_takedown TO anon;
```

## Entity Resolution 알고리즘

1. LLM이 추출한 `(name, road_address)` 받음.
2. **카카오 로컬 검색 API**에 `name + road_address` 쿼리.
3. 결과 1순위의 `placeId`, 좌표, 분류 가져옴.
4. 좌표가 입력 주소의 ±300m 안이면 매칭 성공 → `places.kakao_place_id` 키로 upsert.
5. 매칭 실패면:
   - `natural_key = normalize(name) + ':' + geohash(lat, lng, 7)` 자체 생성.
   - normalize: 공백 제거 + 괄호 안 지점명 추출 + 동음이의 분리(`(시청점)` vs `(역삼점)`).
6. **머지 룰**: 동일 카카오 placeId 발견 시, 기존 natural_key 레코드를 placeId 키로 머지.

상세 정규화 룰은 [PIPELINE.md](PIPELINE.md) 참조.

## 인덱스 전략

- 지도 영역(bbox) 조회 → `places.latitude, longitude`에 GiST 또는 (lat, lng) 복합.
- 등급별 필터 → `place_grade_v1.grade`에 BTree.
- 방문 히스토리 → `place_visits (place_id, visit_date DESC)`.
- 기관 통계 → `place_visits (agency_id, visit_date)`.

## 백업·복원

- Supabase 자동 백업(Pro plan): 매일.
- 별도: GitHub Actions가 주 1회 `pg_dump` 후 별도 저장소에 commit (작은 스키마라 가능).
