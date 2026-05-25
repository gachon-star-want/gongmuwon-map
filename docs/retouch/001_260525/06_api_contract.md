# 06. API 계약

## 목적

리터치 UI에 필요한 API를 정의하되, 기존 공개 API의 breaking change를 막는다.

## 읽는 대상

- API route 구현자
- 프론트엔드 구현자
- OpenAPI/llms.txt 문서 담당자

## 완료 기준

- 기존 `GET /api/v1/places`는 현재 계약을 유지한다.
- 신규 UI 전용 API `GET /api/v1/places/search`, `GET /api/v1/regions`를 추가한다.
- API 응답은 공공누리 출처 표시와 법적 표기 정책을 해치지 않는다.

## 원칙

- 기존 공개 API는 서드파티와 AI 에이전트가 사용할 수 있으므로 breaking change를 하지 않는다.
- 신규 UI 요구는 새 endpoint로 해결한다.
- 모든 공개 GET endpoint는 `*_public` view 또는 그에 준하는 마스킹된 데이터만 반환한다.
- 개인 실명은 API 응답 단계에서 마스킹하지 않는다. DB 적재 단계에서 이미 마스킹되어 있어야 한다.
- 댓글·평점·후기 필드는 이번 지도 리터치 API 범위에 만들지 않는다. 운영자가 커뮤니티 기능을 도입하기로 결정하면 ADR, 법무 문서, 모더레이션 정책을 먼저 갱신한 뒤 별도 API로 설계한다.
- 광고 수익화용 설정은 식당 공개 데이터 API와 섞지 않는다. 필요하면 별도 정적 설정 또는 환경변수 기반 UI 설정으로 처리한다.

## 기존 API 유지

### `GET /api/v1/places`

현재 역할:

- bbox 기반 식당 목록 조회
- grade 필터
- limit 제한

유지해야 하는 것:

- `bbox`, `grade`, `limit` query 지원
- 응답 필드 이름 유지
- 정렬 기본값 유지: `score desc`, `last_visit_at desc`
- CORS와 public cache 유지

추가 금지:

- `q`, `region`, `sort`를 이 endpoint에 억지로 추가해 기존 의미를 흐리지 않는다.
- 응답에서 기존 필드를 제거하거나 타입을 바꾸지 않는다.

## 신규 API 1: `GET /api/v1/places/search`

### 용도

홈 UI의 검색, 자치구 필터, 등급 필터, 정렬, 결과 목록을 위한 endpoint.

### Query

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `q` | string | no | 없음 | 식당명, 주소, 카테고리, 부서명 통합 검색 |
| `region` | string | no | 전체 | `서울 강남구` 또는 comma-separated |
| `grade` | string | no | `★★★,★★,✦` | `★★★`, `★★`, `★`, `✦` comma-separated |
| `sort` | string | no | `score` | `score`, `recent`, `visits` |
| `limit` | number | no | 50 | 1-100 |
| `cursor` | string | no | 없음 | 다음 페이지 cursor |

### 검색 규칙

- `q`는 trim 후 빈 문자열이면 검색 조건에서 제외한다.
- 식당명 prefix/부분 매칭을 최우선으로 한다.
- 주소와 카테고리 매칭은 보조 점수로 둔다.
- 부서명 검색은 `place_visits_public` 또는 집계 view를 통해 마스킹된 부서명만 대상으로 한다.
- `region`은 `places_public.road_address_part`와 정확히 매칭한다.

### 정렬

| sort | ORDER BY |
|---|---|
| `score` | score desc nulls last, last_visit_at desc nulls last |
| `recent` | last_visit_at desc nulls last, score desc nulls last |
| `visits` | visit_count_12m desc nulls last, unique_department_count_12m desc nulls last |

### 200 응답

```json
{
  "items": [
    {
      "id": "8c5e2f3a-0000-0000-0000-000000000000",
      "name": "창고43 시청점",
      "road_address": "서울 중구 서소문로 120",
      "road_address_part": "서울 중구",
      "latitude": 37.5658,
      "longitude": 126.9784,
      "category": "음식점 > 한식",
      "is_closed": false,
      "closure_report_count": 0,
      "score": 6.32,
      "grade": "★★★",
      "last_visit_at": "2026-04-12",
      "visit_count_12m": 12,
      "unique_department_count_12m": 5,
      "unique_agency_count_12m": 2,
      "avg_amount_per_person": 18300,
      "matched_fields": ["name"]
    }
  ],
  "next_cursor": null,
  "source_notice": "공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외"
}
```

### 날짜 처리

- API는 기존 관례대로 date string `YYYY-MM-DD`를 반환한다.
- UI 표시 단계에서 `YYYY.MM.DD`로 변환한다.

### 에러

| 상태 | 조건 |
|---|---|
| 400 | `sort`, `limit`, `grade` 값이 허용 범위를 벗어남 |
| 405 | GET 외 method |
| 500 | DB 오류 |

## 신규 API 2: `GET /api/v1/regions`

### 용도

자치구 필터 option, region별 count, 지도 초기 bounds 보정에 사용한다.

### Query

| 이름 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `include_empty` | boolean | no | 데이터가 없는 자치구도 반환할지 여부 |

### 200 응답

```json
{
  "items": [
    {
      "region": "서울 강남구",
      "label": "강남구",
      "place_count": 124,
      "top_place_count": 12,
      "recommended_place_count": 28,
      "new_place_count": 7,
      "center": { "latitude": 37.5172, "longitude": 127.0473 },
      "bbox": {
        "min_latitude": 37.456,
        "min_longitude": 127.010,
        "max_latitude": 37.535,
        "max_longitude": 127.125
      },
      "last_visit_at": "2026-04-12"
    }
  ],
  "source_notice": "공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외"
}
```

## API smoke 대상

아래 요청은 리터치 구현 후 반드시 성공해야 한다.

```text
GET /api/v1/places/search?q=스타벅스&limit=20
GET /api/v1/places/search?region=서울 강남구&grade=★★★
GET /api/v1/places/search?region=서울%20강남구&grade=★★★
GET /api/v1/regions
```

두 번째 줄은 사람이 읽기 쉬운 표기이고, 실제 HTTP 요청에서는 세 번째 줄처럼 공백을 `%20`으로 인코딩한다.

## OpenAPI와 llms.txt

신규 endpoint를 추가하면 다음 파일도 갱신한다.

- `apps/web/public/openapi.json`
- `apps/web/public/llms.txt`
- `apps/web/public/llms-full.txt`

갱신 시 포함할 내용:

- 신규 endpoint 경로와 query parameter
- 공공누리 제1유형 출처 표시
- 등급은 맛 평가가 아니라 방문 빈도와 부서 다양성 기반 통계 신호라는 설명
- 이번 리터치 API에는 댓글·평점·후기 데이터가 없다는 설명

## 캐시

| Endpoint | Cache-Control |
|---|---|
| `/api/v1/places` | 기존 유지 |
| `/api/v1/places/search` | `public, s-maxage=300, stale-while-revalidate=600` |
| `/api/v1/regions` | `public, s-maxage=1800, stale-while-revalidate=3600` |

## 보안과 개인정보

- 공개 GET endpoint는 service role이 아닌 readonly connection을 사용한다.
- 응답에는 raw excerpt, extractor metadata, reporter fingerprint, takedown request 정보를 포함하지 않는다.
- 실명 마스킹 정책에 어긋나는 컬럼이 필요하면 endpoint 추가 전에 데이터 모델과 법무 문서를 먼저 수정해야 한다.
