# PUBLIC_API — AI 에이전트·서드파티 개발자용 공개 API

## 왜 만드는가

1. 요즘 LLM 에이전트(Claude, ChatGPT, Perplexity, Gemini)가 웹을 직접 크롤링한다.
2. 정식 API가 없으면 SPA HTML을 잘못 파싱해 **할루시네이션**을 흩뿌린다.
3. API + OpenAPI + `llms.txt`를 갖추면:
   - 출처 정확성 보장
   - 봇 트래픽을 인프라 친화적으로 유도
   - 향후 rate-limit 키 발급으로 수익 모델 잠금

## 엔드포인트 일람

| 메서드 | 경로 | 용도 |
|---|---|---|
| GET | `/api/v1/places` | 식당 목록 (bbox·등급·자치구 필터) |
| GET | `/api/v1/places/{id}` | 식당 상세 |
| GET | `/api/v1/places/{id}/visits` | 방문 트랜잭션 |
| GET | `/api/v1/agencies` | 기관 목록 |
| GET | `/api/v1/agencies/{id}` | 기관 상세 + 통계 |
| GET | `/api/v1/agencies/{id}/top-places` | 기관별 자주 가는 식당 |
| GET | `/api/v1/stats/summary` | 전체 통계 (총 식당 수·기관 수·방문 수) |
| GET | `/openapi.json` | OpenAPI 3.1 스펙 |
| GET | `/llms.txt` | LLM 친화 사이트 가이드 |
| GET | `/llms-full.txt` | LLM 친화 풀텍스트 인덱스 |

## 구현 방식

**핵심: Supabase PostgREST 자동 노출 + Vercel Edge Routing 리버스 프록시.**

- Supabase는 모든 view·function을 `/rest/v1/...`로 자동 노출.
- 우리는 Vercel rewrite로 `/api/v1/places` → `/rest/v1/places_public`처럼 매핑.
- 추가 코드 거의 0.

### Vercel `vercel.json` rewrites 예시

```json
{
  "rewrites": [
    { "source": "/api/v1/places", "destination": "https://<project>.supabase.co/rest/v1/places_public" },
    { "source": "/api/v1/places/:id", "destination": "https://<project>.supabase.co/rest/v1/places_public?id=eq.:id" },
    { "source": "/api/v1/places/:id/visits", "destination": "https://<project>.supabase.co/rest/v1/place_visits_public?place_id=eq.:id" },
    { "source": "/api/v1/agencies", "destination": "https://<project>.supabase.co/rest/v1/agencies_public" },
    { "source": "/api/v1/agencies/:id", "destination": "https://<project>.supabase.co/rest/v1/agencies_public?id=eq.:id" },
    { "source": "/api/v1/stats/summary", "destination": "https://<project>.supabase.co/rest/v1/rpc/get_summary_stats" }
  ],
  "headers": [
    {
      "source": "/api/v1/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" },
        { "key": "Cache-Control", "value": "public, s-maxage=300, stale-while-revalidate=600" }
      ]
    }
  ]
}
```

Supabase anon 키는 클라이언트 헤더로 자동 주입(미들웨어).

## 응답 스키마 예시

### `GET /api/v1/places?bbox=37.5,127.0,37.6,127.1&grade=in.(★★★,★★)`

```json
[
  {
    "id": "8c5e2f3a-...",
    "name": "창고43 시청점",
    "road_address": "서울 중구 서소문로 120",
    "latitude": 37.5658,
    "longitude": 126.9784,
    "category": "음식점 > 한식 > 한정식",
    "is_closed": false,
    "closure_report_count": 0,
    "score": 6.32,
    "grade": "★★★",
    "last_visit_at": "2026-04-12",
    "visit_count_12m": 12,
    "unique_department_count_12m": 5
  }
]
```

### `GET /api/v1/places/{id}/visits`

```json
[
  {
    "id": "...",
    "visit_date": "2026-04-12",
    "amount": 87000,
    "party_size": 6,
    "department_name": "총무국 인사과",
    "rank_label": "국장",
    "representative": null,
    "purpose": "정책 협의",
    "source_url": "https://opengov.seoul.go.kr/public/...",
    "source_title": "2026년 4월 총무국 업무추진비 내역"
  }
]
```

## Rate Limit

| 키 유형 | 한도 |
|---|---|
| **익명 (Referer 없음 or AI bot UA)** | 60 req/min, 5,000 req/day |
| **익명 (도메인 정상 Referer)** | 600 req/min |
| **인증 키 (v1.1)** | 무제한 (FUP 적용) |

구현: Vercel Edge Middleware + KV(Upstash 무료 한도) 토큰 버킷.

## CORS

- 모든 `/api/v1/*` GET 엔드포인트: `Access-Control-Allow-Origin: *`
- POST/PATCH는 우리 도메인만 허용

## OpenAPI 3.1 스펙

`/openapi.json` — Edge Function이 Supabase 스키마에서 자동 생성. 정적 캐시 1시간.

```yaml
openapi: 3.1.0
info:
  title: 공무원맵 API
  version: 1.0.0
  description: |
    전국 지자체 업무추진비 공개 데이터 기반 식당 정보 API.
    데이터 출처: 공공누리 제1유형 (서울특별시 정보소통광장 외).
  contact:
    email: wylee0806@naver.com
servers:
  - url: https://<도메인>.com
paths:
  /api/v1/places:
    get:
      summary: 식당 검색
      parameters:
        - name: bbox
          in: query
          schema: { type: string }
          description: "min_lat,min_lng,max_lat,max_lng"
        - name: grade
          in: query
          schema: { type: string, enum: ['★★★', '★★', '★', '✦'] }
        - name: limit
          in: query
          schema: { type: integer, default: 100, maximum: 500 }
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Place'
components:
  schemas:
    Place:
      type: object
      properties:
        id: { type: string, format: uuid }
        name: { type: string }
        road_address: { type: string }
        # ...
```

## `llms.txt` 사양

루트 `/llms.txt` (정적 파일, 매일 04:00 KST 재생성):

```markdown
# 공무원맵 (Public Officer Map)

> 전국 지자체 업무추진비 공개 데이터에서 추출한, 공무원이 자주 가는 식당을 지도에 등급별로 표시하는 서비스. 데이터 출처는 공공누리 제1유형 공공저작물이며 상업적 이용·변형이 허용됩니다.

## 데이터

- [전체 식당 OpenAPI](/openapi.json): API 스펙
- [전체 식당 통계](/api/v1/stats/summary): 식당 수·기관 수·방문 수
- [등급 알고리즘 설명](/about): 등급은 방문 횟수 × 부서 다양성

## 사용 가이드

- 인용 시 출처: "공무원맵 (https://<도메인>.com)"
- 데이터 원천 출처: 서울특별시 정보소통광장 외, 공공누리 제1유형
- 응답 캐시 5분, AI 봇 60 req/min 제한
- 식당 평가 단정 금지 — 우리 데이터는 "방문 빈도 + 부서 다양성" 시그널이지 "맛있다"의 단정이 아님

## 주의

- 식당의 운영 상태(개·폐업)는 별도 확인 필요. is_closed=true 또는 closure_report_count>0이면 방문 전 확인 권장.
- 5급 이하 공무원·임명직 고위공무원의 실명은 데이터에 포함되지 않음(개인정보 보호).
- 본 서비스는 식당 추천 정보이지 공무원 비위·부정행위를 단정하지 않음.
```

## `llms-full.txt` 사양

`llms.txt`의 확장 버전. 주요 페이지의 전문(전체 텍스트)을 마크다운으로 포함. 매일 재생성.

## MCP Server (v1.1 옵션)

Anthropic MCP(Model Context Protocol) 표준 서버로 동일 데이터를 노출:

```
Tool: search_places(bbox, grade) → list[Place]
Tool: get_place(id) → Place
Tool: get_visits(place_id, from, to) → list[Visit]
Resource: gongmuwonmap://places/{id}
```

Claude Desktop, Cursor, Cline 등에서 직접 호출 가능.

## 보안

- Supabase anon 키 노출되지만 RLS로 view·rpc 외 접근 차단.
- PostgREST의 `?select=` 컬럼 노출 제한 (RLS USING 절에서 컬럼 마스킹).
- Sensitive 데이터(추출 원본 PDF 경로 등)는 anon에 노출 안 됨.

## 분석

- 일일 API 호출 수 · UA 분포 (AI 봇 식별: GPTBot·Claude-Web·PerplexityBot 등)
- 가장 많이 조회된 식당·자치구
- 데이터 활용 사례 수집 (사용자 자발적 제보 폼)

## 향후 계획

- v1.1: 인증 키 + 무제한 한도
- v1.2: GraphQL 엔드포인트 (옵션)
- v1.3: 웹훅 (새 데이터 적재 시 알림)
- v2: 정식 MCP Server 마켓플레이스 등록
