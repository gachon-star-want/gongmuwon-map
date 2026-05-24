# AGENTS.md — 공무원맵 (Public Officer Map)

이 문서는 **모든 AI 에이전트(Codex / Claude Code / Cursor / Amp / Jules / Factory 등)가 작업 시작 시 자동으로 읽는 단일 부팅 파일**입니다. AGENTS.md는 OpenAI · Anthropic · Google · Cursor 등이 공동 제정하고 Agentic AI Foundation(Linux Foundation 산하)이 관리하는 오픈 스펙입니다.

이 프로젝트에서 무언가를 만들거나 수정하기 전에 반드시 `docs/`의 관련 문서를 먼저 읽으십시오.

---

## 한 줄 정의

**전국 지자체가 법령에 의해 의무 공개하는 「업무추진비 집행내역」을 자동 수집·정제하여, 공무원이 자주 가는 식당을 지도에 등급별로 표시하는 시민 서비스.**

핵심 가설: "사장이 광고로 띄우는 맛집"이 아니라 **"공무원이 자기 돈처럼 쓰는 게 아까울 때 진짜 가는 집"** 이 가장 강한 가성비 시그널이다.

---

## v1 스코프 (오늘 배포 목표 아님 — 오늘은 설계 문서만)

- **서울 — 52개 기관**: 서울시청(1) + 서울시의회(1) + 25개 자치구청 + 25개 자치구의회
- **데이터 윈도우**: 최근 12개월 윤산(rolling) + 백필 24개월 (등급엔 12개월만 사용)
- **갱신 주기**: 매일 1회 크롤
- **확장 로드맵**: v2 경기·인천 / v3 충청 / v4 경상 / v5 전라 / v6 강원 / v7 제주

---

## 핵심 결정 한 페이지 (Single Source of Truth)

| 영역 | 결정 | 상세 |
|---|---|---|
| **데이터 출처** | 서울시 정보소통광장 + 자치구·의회 게시판 (PDF/HWP/XLSX) | [ADR-001](docs/adr/ADR-001-data-source-strategy.md) |
| **어댑터 전략** | **전부 LLM 범용 추출** (정확성·속도 우선, 토큰 비용 무제한) | [ADR-002](docs/adr/ADR-002-llm-extraction.md) |
| **식당 정체성** | 카카오 로컬 placeId + (정규화 이름 + 좌표 격자) 폴백 | [ADR-003](docs/adr/ADR-003-entity-resolution.md) |
| **등급 공식** | `score = visit_count × log10(unique_departments + 1)` + 자치구별 백분위 컷오프 | [ADR-004](docs/adr/ADR-004-ranking-formula.md) |
| **지도** | 카카오맵 JS API (placeId 정합성) | [ADR-005](docs/adr/ADR-005-map-provider.md) |
| **스택** | Vite + React + TypeScript + Mantine + Neon(Postgres) + Cloudflare R2 + Vercel(API Routes & Hosting) | [ADR-006](docs/adr/ADR-006-stack.md) · [ADR-010](docs/adr/ADR-010-database-stack-migration.md) |
| **배포** | Vercel(프론트 + API Routes) + Neon(DB) + Cloudflare R2(Storage) + GitHub Actions(매일 크롤) | [ADR-007](docs/adr/ADR-007-deployment-strategy.md) · [ADR-010](docs/adr/ADR-010-database-stack-migration.md) |
| **공개 API** | REST(Vercel API Routes 수기 작성) + OpenAPI 3.1 + `/llms.txt` + (옵션) MCP server | [ADR-008](docs/adr/ADR-008-public-api-and-ai-agents.md) |
| **LLM 라우팅** | **Anthropic + OpenAI + Gemini 멀티 프로바이더** (작업 유형별 1·2·3차 폴백, 일일 예산 가드레일) | [ADR-009](docs/adr/ADR-009-multi-llm-provider-routing.md) |

---

## 표기 정책 (법적 안전선)

| 대상 | 표기 |
|---|---|
| 선거직 고위공무원 (시장·구청장·시의원·구의원) | **실명 + 직급** OK |
| 임명직 고위공무원 (부시장·국장·과장) | **직급 + 부서**, 실명 마스킹 |
| 5급 이하 | **부서명 + "○○과 외 N명"**, 실명·직급 마스킹 |
| 식당명·주소·일자·금액 | 원본 그대로 |
| 사용자 댓글·평점·후기 | **v1엔 없음** (명예훼손 리스크) |
| 데이터 출처 | 푸터 명시 — "공공누리 제1유형, 출처: 서울특별시 정보소통광장 외" |

근거 및 상세: [docs/LEGAL_PRIVACY.md](docs/LEGAL_PRIVACY.md), [docs/RISK_MITIGATION.md](docs/RISK_MITIGATION.md)

---

## 문서 인덱스

작업할 영역에 따라 아래 문서를 먼저 읽으십시오.

| 작업 영역 | 읽을 문서 |
|---|---|
| 무엇·왜를 이해 | [PRD.md](docs/PRD.md) |
| 전체 시스템 구조 | [ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| DB·스키마·entity resolution | [DATA_MODEL.md](docs/DATA_MODEL.md) |
| 크롤러·파서·정규화 | [PIPELINE.md](docs/PIPELINE.md) |
| 등급 계산 | [ALGORITHM.md](docs/ALGORITHM.md) |
| 프론트·지도·필터·디테일 패널 | [UI_UX.md](docs/UI_UX.md) |
| 도구 선택 근거 | [TECH_STACK.md](docs/TECH_STACK.md) |
| AI 에이전트·서드파티용 API | [PUBLIC_API.md](docs/PUBLIC_API.md) |
| 법령·공공누리·표기 정책 | [LEGAL_PRIVACY.md](docs/LEGAL_PRIVACY.md) |
| 민원·가처분·노티스앤테이크다운 | [RISK_MITIGATION.md](docs/RISK_MITIGATION.md) |
| 자율 모드 실행 순서 | [RUNBOOK.md](docs/RUNBOOK.md) |
| 검증 시나리오 | [TEST_PLAN.md](docs/TEST_PLAN.md) |
| 버전 로드맵 | [CHANGELOG.md](docs/CHANGELOG.md) |

ADR(돌이킬 수 없는 결정 박제)은 `docs/adr/` 폴더 참조.

---

## 작업할 때 지켜야 할 규칙

1. **결정 사항을 바꿔야 한다면** → 임의 변경 금지. ADR을 새로 작성해서 이전 ADR을 "Superseded by" 처리.
2. **데이터 노출 정책은 LEGAL_PRIVACY.md가 최종 권위** — 이걸 어기는 코드는 머지 금지.
3. **사용자 댓글·평점·후기 기능 v1엔 절대 금지** — 명예훼손 리스크. v2 결정 전까지 추가하지 말 것.
4. **개인 실명은 데이터 적재 단계에서 마스킹** — 절대 DB에 저장 후 표시 단계 마스킹하지 말 것. 유출 리스크.
5. **운영자 신원**은 아래 확정값을 사용한다. 자율 에이전트가 임의로 변경하지 말 것.
6. **공공누리 출처 표시** — 푸터·OpenAPI 스펙·llms.txt에 누락 없이.

---

## 운영자 정보

```
실명/단체명: 이원영/WonYoungLee
대표 이메일: wylee0806@naver.com
연락처(가처분 송달용): 010-7133-0806
주소: 경기도 성남시 분당구 수내로 39
- 사업자등록번호: (해당 없음 — 개인 운영. 사업자 등록 시 LEGAL_PRIVACY.md 업데이트 필요)
- 도메인 (primary): xn--ob0bo0wl1ax52a.com
- 도메인 (alias): (없음)
```
