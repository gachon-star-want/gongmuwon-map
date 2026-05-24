# 작업 메모리

## 2026-05-24 재개 체크포인트

- Phase 1 완료 증거:
  - Neon project: `round-wind-92313772` (`gongmuwon-map`)
  - R2 bucket: `officer-map-raw`
  - Seoul City Hall 적재: `place_visits=175`, `places=148`
  - `places_public` readonly role 조회 성공: `148`
  - `place_grade_v1` graded rows: `148`
  - representative 정책 위반: `0`
  - Kakao match rate: `89.19%`
- 검증 완료:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 7 passed
  - `npm run build` → passed
  - API TypeScript compile → passed
  - MD `<<TBD` grep → 0건
- GitHub 백업:
  - `4ef4fc2` — Neon/Vercel API Routes 전환
  - `a08a97f` — Kakao placeId 중복 upsert 수정
- 현재 진행:
  - Phase 2 프론트 MVP 작업 중
  - 로컬 미커밋 변경: `apps/web/src/App.tsx`, `apps/web/src/styles.css`
- 주의:
  - 실제 Phase 1 적재는 deterministic normalizer로 수행. Anthropic 응답 비JSON 케이스는 parser 보강 완료.
  - Phase 2의 51개 기관 백필은 아직 구현/검증 전. 먼저 52기관 마스터/백필 실행 구조와 프론트 MVP 검증이 필요.

## 2026-05-24 Phase 2 프론트 중간 체크포인트

- 구현 완료:
  - React/Mantine 기반 지도형 MVP로 교체
  - `/api/v1/places`, `/api/v1/places/{id}/visits` fetch 연결
  - 자치구, 등급, 폐업 포함, 검색, 상세/목록 패널 필터 동작 구현
  - Kakao JS 키가 있으면 카카오맵, 없으면 좌표 기반 fallback map 사용
  - 폐업 신고 모달 → `POST /api/closure-report` 연결
  - `/api/v1/stats/summary`, `/api/sitemap`, 정적 `/llms.txt`, `/llms-full.txt`, `/robots.txt`, `/openapi.json` 추가
- 검증 완료:
  - `npm run build` → passed
  - API TypeScript compile → passed
- 다음 작업:
  - Vercel env에 Neon/R2/Kakao/cron 값 주입
  - production deploy 후 API/프론트 렌더링 QA
  - 52기관 백필은 현재 서울 정보소통광장 단일 크롤러만 있어, 기관 마스터 생성 + 백필 구조 또는 제한적 대체 검증 필요
