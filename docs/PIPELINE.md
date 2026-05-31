# PIPELINE — 크롤 → 파싱 → 정규화 → 지오코딩 → 적재

## 전체 그림

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Crawler    │ → │  Fetcher     │ → │  Extractor   │ → │  Normalizer  │
│ (게시판 리스트)│   │ (첨부 다운로드)│   │ (PDF→TXT 등)  │   │  (LLM JSON)  │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
                                                                │
                                                                ▼
                  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
                  │   Loader     │ ← │   Geocoder   │ ← │   Resolver   │
                  │ (Neon upsert │   │ (카카오 좌표) │   │ (카카오 place│
                  │ via psycopg) │   │              │   │   match)     │
                  └──────────────┘   └──────────────┘   └──────────────┘
```

각 단계는 멱등성을 가지며, 중간 산출물은 Cloudflare R2(`r2://officer-map-raw/`)와 로컬 SQLite(`pipeline_state.db`)에 캐시.

## 모듈별 책임

### 1. `crawler/` — 게시판 리스트 수집

- **입력**: agency_id, 마지막 크롤 시각
- **출력**: 신규/갱신된 게시물의 `(agency_id, source_url, title, published_at, file_links[])` 리스트

#### 어댑터 유형
| 유형 | 사이트 예 | 구현 |
|---|---|---|
| **HTML 표 직접** | 서울 정보소통광장 (`opengov.seoul.go.kr/expense/list`) | httpx + selectolax, `?page=N` 페이징, 상세 페이지 fetch까지 |
| **첨부형 게시판** | 자치구청·의회 일반 게시판 | httpx로 목록 페이지 → 상세 → 첨부파일 링크 추출. JS 렌더링 필요 시 Playwright. |
| **OpenAPI 보조** | 서울 열린데이터광장 (서비스 종료 안내 있으나 백업용) | requests + 키 인증 |

#### 어댑터 인터페이스
```python
class CrawlerAdapter(Protocol):
    agency_id: UUID

    async def list_posts(self, since: date) -> list[PostRef]: ...
    async def fetch_post(self, ref: PostRef) -> PostDetail: ...  # 첨부 URL·메타 포함
```

#### LLM 기반 어댑터 자동화 (보조)
- 새 지자체 추가 시 사람이 어댑터 코드 작성 안 함.
- `crawler/generic_llm_adapter.py`가 다음을 자동 수행:
  1. 게시판 첫 페이지 fetch
  2. LLM(Sonnet)에 HTML 던지면서 "이 사이트에서 '업무추진비' 관련 게시물 목록 셀렉터와 페이징 패턴을 JSON으로 추론하라" 요구
  3. 결과를 `agencies.source_pattern` jsonb 컬럼에 저장 → 다음 회부터 hand-coded 어댑터처럼 사용
  4. 자동 추론 실패율 > 30%면 GitHub Issue 자동 생성

### 2. `fetcher/` — 첨부 파일 다운로드

- HTTP GET + Range 헤더 + 30초 타임아웃
- 다운로드 DoS 가드:
  - 문서 본문 최대 크기: **25 MiB** (`MAX_DOCUMENT_DOWNLOAD_BYTES`)
  - `Content-Length`가 25 MiB를 초과하면 본문을 읽기 전에 거부
  - `Content-Length`가 없거나 부정확해도 스트리밍 중 누적 본문 크기가 25 MiB를 초과하면 거부
  - curl 폴백은 `--max-filesize`를 사용하고, 응답 파싱 후 본문 크기를 다시 검증
  - 초과 시 `DocumentProcessingLimitError`/`PipelineConfigError`; 조용한 truncate 금지
- SHA-256 해시 계산, 같은 해시 캐시되어 있으면 skip
- Cloudflare R2 버킷 `officer-map-raw` 에 `{agency_id}/{yyyy-mm}/{hash}.{ext}` 키로 업로드 (S3 호환 SDK 사용, `R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` / `R2_BUCKET` 환경변수)
- 비-dry-run 기본 실행은 업로드 후 `storage_path = r2://officer-map-raw/{agency_id}/{yyyy-mm}/{hash}.{ext}`를 `sources`에 저장
- 운영 중단 모드가 아니라면 `--allow-missing-r2` 없이 R2 업로드가 실패하면 전체 run은 config error로 중단됨

### 3. `extractor/` — 파일 → 텍스트

| 파일 형식 | 1차 도구 | 폴백 |
|---|---|---|
| HTML | `selectolax` 표 셀렉터 | LLM에 HTML 그대로 |
| PDF (text-based) | `pdfplumber` (`page.extract_tables()`) | `pdf-to-image` + LLM vision |
| PDF (scanned image) | 바로 LLM vision | — |
| XLSX | `openpyxl` (`load_workbook` + sheet 순회) | LLM에 CSV 변환 후 |
| HWP | `hwp5txt` (CLI) → 텍스트 | LibreOffice CLI로 PDF 변환 후 PDF 파이프 |
| HWPX | XML 파서 (ZIP 내부 `Contents/section0.xml`) | HWP 동일 폴백 |

추출 결과는 **표 (rows[][])** 또는 **자유 텍스트** 둘 중 하나로 정규화. Normalizer가 둘 다 처리 가능.

#### 문서 처리 DoS 가드

공개 문서는 작은 월별 집행내역 파일이라는 전제하에, 파서는 다음 한도를 강제한다.

| 대상 | 한도 | 실패 동작 |
|---|---:|---|
| 다운로드 문서 본문 | 25 MiB | 다운로드 거부 |
| PDF 입력 | 25 MiB | poppler 실행 전 거부 |
| PDF vision 페이지 | 요청값을 1~5쪽으로 clamp | 5쪽 초과 이미지 생성 금지 |
| `pdftotext` / `pdftoppm` | 30초 timeout | `PipelineConfigError` |
| PDF PNG 이미지 | 8 MiB/쪽, 20 MiB/문서 | LLM 전송 전 거부 |
| XLS/XLSX 입력 | 25 MiB | workbook open 전 거부 |
| Spreadsheet sheets | 20 sheets | 순회 전 거부 |
| Spreadsheet rows/columns | 5,000 rows/sheet, 100 columns/sheet | 행 materialize 전/중 거부 |
| Spreadsheet total cells | 100,000 cells/workbook | 전체 nested list 생성 전/중 거부 |

초과 파일은 부분 파싱하거나 truncate하지 않는다. 실패는 명시적 예외로 상위 run/운영 큐가 처리하며, oversized 이미지·스프레드시트 내용은 LLM에 보내지 않는다.

### 4. `normalizer/` — LLM 정규화

#### 정규화 JSON 스키마

```json
{
  "source_id": "<uuid>",
  "agency_id": "<uuid>",
  "visits": [
    {
      "visit_date": "2026-04-12",
      "amount": 87000,
      "party_size": 5,
      "purpose": "정책 협의",
      "department_name": "총무국 인사과",
      "rank_label": "국장",
      "representative": null,
      "payment_method": "법인카드",
      "expense_category": "기관운영업무추진비",
      "place_raw": {
        "name": "창고43 시청점",
        "address_hint": "중구 서소문로 120"
      },
      "raw_excerpt": "...",
      "confidence": 0.92
    }
  ],
  "extractor_model": "claude-haiku-4-5",
  "warnings": []
}
```

#### 모델 라우팅 (멀티 프로바이더 — [ADR-009](adr/ADR-009-multi-llm-provider-routing.md))

3개 프로바이더(Anthropic·OpenAI·Gemini)를 통일 인터페이스 `LLMClient`로 호출. 작업 유형에 따라 라우팅:

| 작업 유형 | 1차 (모델 · thinking/reasoning) | 2차 | 3차 |
|---|---|---|---|
| 대량 표 정규화 | Gemini 3.5 Flash · `thinking_level=minimal` | Claude Haiku 4.5 · ET off | GPT-5.5 · `reasoning.effort=low` |
| PDF 표 추출 (텍스트) | Claude Haiku 4.5 · ET off | Gemini 3.5 Flash · `thinking_level=low` | Claude Sonnet 4.6 · ET 4K |
| PDF 비전(스캔) | **Claude Opus 4.7 vision · ET 8K** | Gemini 3.5 Flash vision · `thinking_level=medium` | GPT-5.5 · `reasoning.effort=medium` |
| 식당명 정규화 | Claude Sonnet 4.6 · ET 4K | GPT-5.5 · `reasoning.effort=medium` | Claude Opus 4.7 · ET 4K |
| 사이트 어댑터 추론 (일회성) | Claude Opus 4.7 · ET 32K | GPT-5.5 · `reasoning.effort=high` | — |
| 마스킹 검증 (보안 critical) | Claude Sonnet 4.6 · ET 16K | Claude Sonnet 4.6 재시도 · ET 16K | 사람 큐 |

> `ET = extended_thinking.budget_tokens`. 프로바이더별 thinking 파라미터 매핑은 [ADR-009](adr/ADR-009-multi-llm-provider-routing.md#thinking--reasoning-파라미터-매핑) 참조.

폴백 트리거: 5xx/429 / 30초 타임아웃 / schema validation 실패 / confidence < 0.8 평균.

호출 단위 토큰 사용량(thinking 토큰 포함)은 `llm_usage`에 시도 단위로 적재한다.
각 시도는 `task_type/provider/model/input_tokens/output_tokens/thinking_tokens/estimated_cost_usd/status/task_id/error_code`를 기록한다.

일일 예산은 환경변수 `LLM_BUDGET_DAILY_USD`를 사용한다.
- 시도 시작 전에 일일 누적비용을 확인한다.
- 상한 초과 시:
  - 현재 시도는 `status='skipped_budget'`으로 기록하고,
  - 아직 사용하지 않은 프로바이더 중 비용이 더 싼 쪽이 있으면 즉시 강등해 재시도한다.
  - 강등 후보가 없으면 `PipelineConfigError("LLM daily budget exceeded")`.

시도 상태값은 다음과 같다.
- `success`: 최종 성공
- `fallback`: 실패/재시도 조건이 발생해 다음 프로바이더로 넘어간 시도
- `error`: 최종 실패한 시도
- `skipped_budget`: 예산 상한으로 인해 스킵된 시도

#### 마스킹 룰 (LLM 시스템 프롬프트에 박힘)

```
1. representative 컬럼은 지역별 선출직 목록에 따라 채운다.
   - 서울: 시장, 구청장, 시의원, 구의원
   - 경기: 도지사, 시장, 군수, 도의원, 시의원, 군의원
   - 인천: 시장, 구청장, 군수, 시의원, 구의원, 군의원
   - "○○○ 시장" → representative = "○○○"
   - "○○○ 시장 외 5명" → representative = "○○○", party_size = 6
2. 임명직 (부시장·부지사·부군수·부구청장·국장·과장·팀장·담당관·전문위원·주무관·직원): rank_label만 채우고 representative = null.
   - "홍길동 국장(총무국)" → department_name = "총무국", rank_label = "국장", representative = null
3. 5급 이하: rank_label = "5급 이하", department_name = 부서명만.
4. 일반 직원 다수 회식: department_name = "○○과 외 N명".
5. 모든 개인 실명 (선거직 제외) 자동 제거.
```

이 룰은 **개별 LLM 호출의 시스템 프롬프트로 박힘** — 추출 결과에 실명이 남으면 schema validator가 reject.

### 5. `entity/` — 식당 ID 매칭

알고리즘은 [DATA_MODEL.md](DATA_MODEL.md#entity-resolution-알고리즘) 참조.

#### 캐싱
- 같은 `(name, address_hint)` 입력은 7일간 카카오 API 결과 캐시 (Redis 없으니 SQLite).
- 카카오 일 30,000회 한도 → 캐시로 95% 이상 절감.

#### `road_address_part` 추출
- 카카오 로컬 API 응답의 `address.region_1depth_name` + `region_2depth_name`을 조합 → `"서울 중구"`, `"서울 강남구"` 형식으로 `places.road_address_part`에 저장.
- 폴백(자체 자연키)인 경우 LLM이 추출한 `address_hint`에서 시·구 패턴(`^서울(특별시)?\s+(\S+구|\S+군|\S+시)`) 정규식으로 분리.
- `road_address_part`는 자치구별 백분위 PARTITION 키([ALGORITHM.md](ALGORITHM.md))의 핵심 컬럼이므로 NOT NULL 보장.

### 6. `geocoder/` — 좌표 보강

- Entity resolver가 placeId 매칭 성공하면 좌표 자동 획득 (별도 호출 불필요).
- 폴백(자체 자연키)인 경우 카카오 주소 → 좌표 변환 API 호출.

### 7. `loader/` — Neon Postgres Upsert

```python
# 의사 코드 (psycopg/asyncpg, DATABASE_URL 사용)
for visit in normalized_batch:
    place = upsert_place(visit.place_raw, resolved)
    upsert_source(visit.source)
    upsert_visit(
        place_id=place.id,
        agency_id=agency_id,
        visit_date=visit.visit_date,
        amount=visit.amount,
        department_name=visit.department_name,
        # ...
        on_conflict=("agency_id", "visit_date", "place_id", "amount", "department_name")
    )
```

- `DATABASE_URL` (service role, RLS bypass) 로 Neon에 직접 SQL 실행. PostgREST 미사용.
- 한 번에 500 row씩 배치 (Neon connection pooler 사용 권장).
- 실패 시 트랜잭션 롤백 + GitHub Issue.

## 실행 스케줄

| 작업 | 빈도 | 트리거 |
|---|---|---|
| `daily-crawl.yml` | 매일 03:00 KST | GitHub Actions cron |
| `GET /api/cron/recompute-grades` | 매일 03:30 KST | Vercel Cron (`vercel.json` crons) |
| `GET /api/sitemap` 워밍 | 매일 04:00 KST | Vercel Cron |
| `data-health-check` | 매일 04:30 KST | GitHub Actions, row count 알림 |

## 에러 처리 정책

- **사이트 다운**: 3회 재시도(지수 백오프), 최종 실패 시 다음 사이클 시도, 24시간 연속 실패 시 알림.
- **파싱 실패**: `extraction_failures` 테이블에 원본 + 에러 적재, 운영자 검토 큐.
- **카카오 API 한도 초과**: 다음 사이클로 미루기 (큐). placeId 못 받으면 자체 natural_key로 적재.
- **LLM 호출 실패**: 30초 타임아웃, 3회 재시도, 다음 모델로 escalate.

## 데이터 품질 검증

- 추출 결과의 `confidence` 분포 모니터링 (평균·p10·p90).
- 일별 신규 row 수 — 7일 평균 대비 ±30% 이상 변동 시 알림.
- 좌표 없는 식당 비율 < 5% 유지.
- 영문 식당명 비율 < 10% (한국어 인코딩 실패 신호).

## 멱등성·재실행

- 모든 단계는 idempotent. 같은 source URL · 같은 hash이면 skip.
- 백필은 `python -m pipeline.backfill --since 2024-01-01 --agency seoul_city` 같이 CLI로.
- 잘못된 추출 정정: `place_visits.extractor_model` 컬럼으로 재처리 대상 식별 가능.
