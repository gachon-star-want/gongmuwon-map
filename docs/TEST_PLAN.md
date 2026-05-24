# TEST_PLAN — 검증 시나리오

## 테스트 계층

| 계층 | 도구 | 범위 |
|---|---|---|
| 단위 | Vitest (web), pytest (pipeline) | 정규화·entity resolution·마스킹 |
| 통합 | pytest + 테스트 DB | 크롤→파싱→적재 end-to-end |
| 데이터 품질 | SQL 쿼리 | row count, NULL ratio, confidence 분포 |
| E2E | Playwright | 사용자 시나리오 (지도·필터·디테일·폼) |
| 수동 QA | 체크리스트 | 30건 데이터 샘플링·법무 페이지·운영자 이메일 |

## 핵심 단위 테스트

### `pipeline/normalizer/test_masking.py`
- 입력: 원본 텍스트 "홍길동 시장 외 5명"
- 기대: `representative="홍길동"`, `party_size=6`, `rank_label="시장"`
- 입력: "박철수 국장(총무국)"
- 기대: `department_name="총무국"`, `rank_label="국장"`, `representative=null`
- 입력: "총무국 외 7명"
- 기대: `department_name="총무국"`, `rank_label="5급 이하"`, `representative=null`

### `pipeline/entity/test_resolver.py`
- 입력: ("창고43 시청점", "중구 서소문로 120")
- 기대: 카카오 placeId 정상 매칭, 좌표 ±300m 안
- 입력: 카카오에 없는 가게
- 기대: natural_key 폴백, normalize("창고43") + geohash

### `pipeline/extractor/test_pdf.py`
- 입력 PDF: text-based 업무추진비 공개 양식
- 기대: 표 행 N개, 컬럼 명세 일치

## 통합 테스트

### `pipeline/test_end_to_end.py`
1. 테스트용 작은 HTML(서울시청 1주일치) → Crawler → Extractor → Normalizer → Loader
2. Supabase 테스트 프로젝트에 적재
3. `place_grade_v1` REFRESH
4. `places_public` 조회 → 등급 정상 부여

### `services/edge-functions/test_takedown.ts`
- POST `/notice-takedown` → `places.hidden_at` 설정 확인
- 같은 fingerprint 중복 신고 차단 확인
- 운영자 이메일 mock 호출 확인

## 데이터 품질 SQL

```sql
-- 1. 마스킹 검증: representative에 시장·구청장·시의원·구의원 외 직급이 들어가면 실패
SELECT COUNT(*) FROM place_visits 
WHERE representative IS NOT NULL 
  AND rank_label NOT IN ('시장','구청장','시의원','구의원');
-- 기대: 0

-- 2. 식별 가능 한글 이름이 department_name에 섞이지 않는지
SELECT COUNT(*) FROM place_visits
WHERE department_name ~ '^[가-힣]{2,4} (외|국장|과장|팀장)';
-- 기대: 0

-- 3. 좌표 결측률
SELECT 100.0 * SUM(CASE WHEN latitude IS NULL THEN 1 ELSE 0 END) / COUNT(*) AS pct
FROM places;
-- 기대: < 5

-- 4. 등급 분포
SELECT grade, COUNT(*) FROM place_grade_v1 GROUP BY grade;
-- 기대: ★★★ 약 10%, ★★ 약 20%, ★ 약 30%, ✦ 변동

-- 5. 데일리 신규 row 수 (7일 이동평균 대비 ±30%)
WITH daily AS (
  SELECT visit_date, COUNT(*) AS n
  FROM place_visits
  WHERE visit_date >= current_date - 30
  GROUP BY visit_date
)
SELECT visit_date, n, AVG(n) OVER (ORDER BY visit_date ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) AS avg7
FROM daily
ORDER BY visit_date DESC;
```

## E2E 시나리오 (Playwright)

### S1: 첫 진입
- `/`로 진입
- 지도 로드 < 2s
- 서울 전체 줌
- 필터 디폴트: 강추·추천·신규 ON

### S2: 마커 클릭
- 지도에서 강추 마커 클릭
- 디테일 패널 슬라이드인
- 식당명·등급·방문 부서·방문 기록 표시
- "원문 PDF 보기" 클릭 → 새 탭에 정부 사이트 열림

### S3: 자치구 필터
- "강남구" 필터 적용
- 지도 마커가 강남구 영역만 표시
- URL에 `?gu=강남구` 파라미터

### S4: 검색
- 식당명 "창고43" 검색
- 자동완성 표시
- 선택 시 지도 이동 + 디테일 패널

### S5: 모바일 바텀시트
- 모바일 viewport(375px)
- 마커 탭 → 바텀시트 peek
- 드래그하면 mid → full

### S6: 폐업 신고
- 디테일 패널 → "폐업 신고" 클릭
- 모달, 사유 선택, 제출
- 토스트 "접수되었습니다"
- 같은 브라우저에서 재시도 → "이미 신고하셨습니다"

### S7: 정보 삭제 요청
- 디테일 패널 → "정보 수정·삭제 요청" 클릭
- 모달, 사유 50자 입력, 제출
- 해당 식당 마커가 지도에서 즉시 사라짐 (hide 적용 확인)

### S8: 접근성
- Tab으로 필터·검색·마커 모두 도달
- Esc로 모달 닫기
- 스크린리더로 마커 라벨 읽기

### S9: 다크모드
- 시스템 다크모드 → 자동 적용
- 명도 대비 검증

### S10: SEO·llms.txt
- 식당 페이지 `/r/창고43-시청점-{uuid}` 직접 접속 → 메타태그 정상
- `/llms.txt`, `/openapi.json`, `/sitemap.xml` 정상

## 수동 QA 체크리스트

### 데이터 정확도 샘플 30건
- 무작위 30개 row를 골라 원본 PDF·HTML과 1:1 비교
- 식당명·금액·일자·부서명 일치율 ≥ 95%

### 법무 페이지 검수
- `/about`, `/privacy`, `/terms`, `/disclaimer`, `/legal` 모두 접속
- `<<TBD>>` grep 결과 0건
- 운영자 신원·이메일·연락처·주소 정확
- 공공누리 출처표시 포함

### 운영자 알림 동작
- 폐업 신고·삭제 요청 폼 제출 → 운영자 이메일 수신 확인
- 이메일에 신청 내용·식당 ID·복원 링크 포함

### 보안
- Supabase service key가 클라이언트 번들에 노출되지 않음
- 카카오 REST key가 클라이언트에 노출되지 않음 (Edge Function 내부만)
- CSP 헤더 검사

## 성능

| 항목 | 목표 |
|---|---|
| LCP (모바일 4G) | < 2.5s |
| 지도 첫 마커 표시까지 | < 1.5s |
| API 응답 (p95) | < 300ms |
| 머티리얼라이즈드 뷰 refresh | < 60s |

## CI

`.github/workflows/`:
- `pipeline-test.yml`: PR마다 pytest 실행
- `web-test.yml`: PR마다 vitest + Playwright 실행
- `daily-crawl.yml`: cron 03:00 KST
- `data-quality.yml`: cron 04:30 KST, SQL 검증, 임계값 위반 시 Slack

## 회귀 방지

- 마스킹 정책 변경 시 → 단위 테스트 추가 후에만 머지
- 등급 공식 변경 시 → ADR 새로 작성 + A/B 테스트
- 새 데이터 소스 추가 시 → 첫 100건 수동 샘플링 검증
