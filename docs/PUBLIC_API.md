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
| GET | `/api/v1/places/search` | UI/LLM 검색용 식당 목록 |
| GET | `/api/v1/places/{id}` | 식당 상세 |
| GET | `/api/v1/places/{id}/visits` | 방문 트랜잭션 |
| GET | `/api/v1/places/{id}/reactions` | 공식 지표와 분리된 좋아요/싫어요 반응 요약 |
| POST | `/api/v1/places/{id}/reactions` | 로그인 사용자의 좋아요/싫어요 반응 저장·해제 |
| GET | `/api/v1/agencies` | 기관 목록 |
| GET | `/api/v1/agencies/{id}` | 기관 상세 + 통계 |
| GET | `/api/v1/regions` | 자치구 목록 + 지역 통계 |
| GET | `/api/v1/stats/summary` | 전체 통계 (총 식당 수·기관 수·방문 수) |
| GET | `/openapi.json` | OpenAPI 3.1 스펙 |
| GET | `/llms.txt` | LLM 친화 사이트 가이드 |
| GET | `/llms-full.txt` | LLM 친화 풀텍스트 인덱스 |

## 구현 방식

**핵심: Vercel API Routes에 v1 엔드포인트를 손으로 작성. 핸들러가 Neon에 SQL 실행 후 `*_public` 뷰 결과를 JSON으로 반환.** ([ADR-010](adr/ADR-010-database-stack-migration.md))

- v1엔 PostgREST 자동 노출이 없으므로 엔드포인트별 짧은 핸들러를 직접 둔다.
- 핸들러는 `DATABASE_URL_READONLY` (anon RLS-restricted Neon 역할)로 연결 → `*_public` 뷰만 SELECT 가능. 이 변수 미설정은 배포 오류로 간주되어 서비스는 시작되지 않는다.
- 쓰기 경로(`/api/closure-report`, `/api/takedown-request`)만 `DATABASE_URL` (service role)로 전환 후 SQL 함수 호출.
- **v1.1 옵션**: Render에 PostgREST 컨테이너 셀프호스트 → 다시 자동 노출로 회귀 검토.

### Vercel API Route 예시 (`api/v1/places.ts`)

```ts
import type { VercelRequest, VercelResponse } from '@vercel/node';
import { Pool } from 'pg';

const pool = new Pool({ connectionString: process.env.DATABASE_URL_READONLY });

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const { bbox, grade, limit = '100' } = req.query;
  // bbox is optional. When omitted, return the nationwide coordinate-bearing list.
  const parsedBbox = bbox ? String(bbox).split(',').map(Number) : null;
  const grades = grade ? String(grade).split(',') : [];
  // 실제 구현은 bbox/grade 조건과 parameter index를 요청된 경우에만 추가한다.
  const { rows } = await pool.query(
    `SELECT * FROM places_public
     WHERE latitude IS NOT NULL
       AND longitude IS NOT NULL
     ORDER BY score DESC NULLS LAST
     LIMIT $1`,
    [Number(limit)],
  );

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 'public, s-maxage=300, stale-while-revalidate=600');
  res.json(rows);
}
```

### 캐시/CORS 헤더 정책

`Access-Control-Allow-Origin`과 `Cache-Control`은 `vercel.json`에서 `/api/v1/*`에 일괄 적용하지 않고, 각 라우트가 직접 설정한다. 공개 읽기 라우트는 `publicReadRoute(..., { cache: ... })`를 사용한다.

- 공개 읽기 GET 엔드포인트(`places`, `places/search`, `regions` 등): 라우트별 `public, s-maxage=..., stale-while-revalidate=...`
- `GET/POST /api/v1/places/{id}/reactions`: 로그인 사용자 상태(`user_reaction`)를 포함할 수 있으므로 `Cache-Control: private, no-store`

> 표 상단의 `/api/v1/*` 경로는 v1 정식 경로이며, 실제 라우트 파일은 Vercel 기본 규칙에 맞춰 repo root `api/v1/...`에 둔다.

## 응답 스키마 예시

### `GET /api/v1/places?grade=★★★,★★`

`bbox=min_lat,min_lng,max_lat,max_lng`는 선택값이다. 생략하면 전국 좌표 보유 식당 목록을 점수순으로 조회한다.

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

현재 v1 코드에는 악용 가능성이 높은 쓰기성 엔드포인트에 대해 API Route 내부 인메모리 fixed-window 제한을 둔다. 키는 서버가 관측한 첫 `x-forwarded-for` IP + User-Agent를 기본으로 하며, 인증 사용자가 확인된 경로는 user id를 함께 포함한다. 응답은 제한 초과 시 `429 { "error": "rate_limited" }`, `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`을 반환한다.

아래 표의 쓰기성 엔드포인트 중 인증·신고·커뮤니티 작성 경로는 Cloudflare Turnstile 토큰도 요구한다. 프론트엔드는 `turnstile_token`을 JSON body에 포함하고, API Route는 `TURNSTILE_SECRET_KEY`로 Siteverify를 호출한다. 서버 secret이 없거나 토큰 검증이 실패하면 요청은 DB 쓰기 전에 fail-closed 된다. `POST /api/v1/places/{id}/reactions`는 로그인 세션과 별도 rate limit만 적용하며 이번 Turnstile 1차 범위에는 포함하지 않는다.

| 경로 | 한도 |
|---|---|
| `POST /api/auth/login` | 10/min per IP+UA+normalized handle |
| `POST /api/auth/register` | 5/hour per IP+UA |
| `POST /api/takedown-request` | 5/hour per IP+UA |
| `POST /api/closure-report` | 20/hour per IP+UA |
| `POST /api/community/posts` | 10/hour per IP+UA/user |
| `POST /api/community/posts/{id}/comments` | 30/hour per IP+UA/user |
| `POST /api/v1/places/{id}/reactions` | 60/min per IP+UA/user |

주의: 이 제한은 Vercel serverless warm instance별 최선 노력(best-effort) 보호다. 다중 인스턴스·리전 전체에서 일관된 제한이 필요하면 이후 Cloudflare/WAF 또는 공유 KV/Redis 기반 edge limiter를 추가해야 한다. 공개 읽기 API 봇 트래픽 제한도 동일하게 edge/WAF 계층에서 별도 적용하는 것이 권장된다.

## CORS

- 공개 읽기 `/api/v1/*` GET/HEAD/OPTIONS 엔드포인트: 라우트 레벨에서 `Access-Control-Allow-Origin: *`
- POST/PATCH는 라우트 레벨에서 우리 도메인만 허용

## OpenAPI 3.1 스펙

`/openapi.json` — 빌드 시 정적 파일로 생성(`apps/web/public/openapi.json`) 또는 `/api/openapi` Vercel API Route가 동적 응답. 1시간 캐시.

```yaml
openapi: 3.1.0
info:
  title: 공무원맵 API
  version: 1.0.0
  description: |
    v1은 서울 52개 기관 중 지도 집계에 반영된 51개 기관의 업무추진비 공개 데이터 기반 식당 정보 API.
    2026-06-01 기준 전국 출처 등록부는 P1-P4 2,200개 기관 중 137개 공식 출처 검증 완료, 1,996개 검증 대기, 67개 법적 검토 보류 상태.
    데이터 출처: 공공누리 제1유형 (서울특별시 정보소통광장 외 수도권·대전·전남·충남 지자체·의회 공식 공개자료).
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
          description: "Optional min_lat,min_lng,max_lat,max_lng. Omit for nationwide coordinate-bearing list."
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

> v1은 서울 52개 기관 업무추진비 공개 데이터에서 추출한, 공무원이 자주 가는 식당을 지도에 등급별로 표시하는 서비스입니다. 2026-05-25 기준 51개 기관이 지도 집계에 반영되어 있습니다. 데이터 출처는 공공누리 제1유형 공공저작물이며 상업적 이용·변형이 허용됩니다.

## 데이터

- [전체 식당 OpenAPI](/openapi.json): API 스펙
- [전체 식당 통계](/api/v1/stats/summary): 식당 수·기관 수·방문 수
- [등급 알고리즘 설명](/about): 등급은 방문 횟수에 부서 다양성 가중치(log10)를 적용한 통계 신호

## 사용 가이드

- 인용 시 출처: "공무원맵 (https://<도메인>.com)"
- 데이터 원천 출처: 서울특별시 정보소통광장 외, 공공누리 제1유형
- 공개 읽기 API는 라우트별 캐시(기본 5분), `/api/v1/places/{id}/reactions`는 `private, no-store`, AI 봇 60 req/min 제한
- 식당 평가 단정 금지 — 우리 데이터는 "방문 빈도 + 부서 다양성 가중치" 시그널이지 "맛있다"의 단정이 아님
- `/api/v1/places/{id}/reactions`는 로그인 기반 좋아요/싫어요 반응이며 공식 등급·방문 통계와 분리된다.

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

- DB 자격 증명은 클라이언트에 노출되지 않음 (모든 SQL은 Vercel API Route 서버 측에서 실행).
- 읽기 핸들러는 `DATABASE_URL_READONLY` (Neon `anon` RLS-restricted) 사용 → 원본 테이블 SELECT 차단, `*_public` 뷰만 허용. `DATABASE_URL_READONLY`가 없으면 시작 시 실패한다.
- 쓰기 핸들러는 `DATABASE_URL` (service role)로 전환 후 SQL 함수만 호출.
- Sensitive 데이터(추출 원본 R2 경로 등)는 anon 응답 스키마에서 제외.

## 분석

- 일일 API 호출 수 · UA 분포 (AI 봇 식별: GPTBot·Claude-Web·PerplexityBot 등)
- 가장 많이 조회된 식당·자치구
- 데이터 활용 사례 수집 (사용자 자발적 제보 폼)

## 향후 계획

- v1.1: 인증 키 + 무제한 한도
- v1.2: GraphQL 엔드포인트 (옵션)
- v1.3: 웹훅 (새 데이터 적재 시 알림)
- v2: 정식 MCP Server 마켓플레이스 등록
