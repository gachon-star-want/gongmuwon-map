# UI/UX 리터치 001 — 2026.05.25

## 목적

공무원맵 홈 화면을 기존 3열 패널형 화면에서 **지도 우선(full-bleed) 탐색 경험**으로 리터치하기 위한 구현 기준을 한 폴더에 모은다.

## 읽는 대상

- 프론트엔드 구현자
- API route 구현자
- QA 담당자
- 이후 UI/UX 결정을 검토할 AI 에이전트

## 완료 기준

- 이 폴더의 문서만 읽어도 리터치 구현 범위, 제약, API 계약, 검증 기준을 이해할 수 있다.
- `docs/PRD.md`, `docs/UI_UX.md`, `docs/LEGAL_PRIVACY.md`, `docs/PUBLIC_API.md`의 핵심 결정을 어기지 않는다.
- 광고 수익화는 금지하지 않는다. 단, 이번 리터치의 핵심 목표는 지도 탐색 UX이며 광고는 지도 조작과 출처 확인을 방해하지 않는 별도 수익화 layer로 설계한다.
- 사용자 댓글·평점·후기·커뮤니티 기능은 현행 `docs/LEGAL_PRIVACY.md`, `docs/RISK_MITIGATION.md`, 루트 `AGENTS.md`와 충돌하므로 이번 UI 리터치 PR에서 몰래 추가하지 않는다. 운영자가 도입하기로 결정하면 ADR과 법무 문서를 먼저 갱신한 뒤 별도 PR로 구현한다.

## 문서 읽는 순서

| 순서 | 문서 | 역할 |
|---|---|---|
| 1 | [01_reference_analysis.md](01_reference_analysis.md) | 거지맵 캡처에서 가져올 UI 패턴과 버릴 패턴을 구분한다. |
| 2 | [02_product_requirements.md](02_product_requirements.md) | 제품 요구사항, 법적 제약, 핵심 비목표를 확정한다. |
| 3 | [03_information_architecture.md](03_information_architecture.md) | 데스크탑·모바일 화면 구조와 상태 전이를 정의한다. |
| 4 | [04_interaction_spec.md](04_interaction_spec.md) | 검색, 필터, 마커, 상세, 신고 모달, URL 동기화를 정의한다. |
| 5 | [05_visual_design_spec.md](05_visual_design_spec.md) | 마커, 클러스터, 패널, 타이포그래피, 반응형 기준을 정의한다. |
| 6 | [06_api_contract.md](06_api_contract.md) | 기존 API 유지와 신규 UI 전용 API 계약을 정의한다. |
| 7 | [07_implementation_plan.md](07_implementation_plan.md) | 실제 코드 변경 순서와 컴포넌트 분리 기준을 정의한다. |
| 8 | [08_test_and_acceptance.md](08_test_and_acceptance.md) | 빌드, API smoke, 데스크탑·모바일 QA, 회귀 검증을 정의한다. |

## 최종 산출물

- 홈(`/`)은 지도 자체가 첫 화면의 주인공인 full-bleed 화면이어야 한다.
- 기존 3열 grid는 제거한다.
- 데스크탑은 floating search/filter와 right drawer를 사용한다.
- 모바일은 bottom nav와 bottom sheet를 사용한다.
- 홈 footer는 화면을 차지하는 정적 footer가 아니라 작은 source pill로 축소한다.
- `/about`, `/privacy`, `/terms`, `/disclaimer`, `/legal`, `/api`의 정적 문서 footer는 유지한다.
- 검색·필터·정렬·선택 상태는 URL query와 동기화한다.
- `selectedPlace`는 초기 진입 시 자동 선택하지 않는다.
- 낮은 줌에서는 클러스터를 우선 표시하고, 확대 시 개별 마커를 표시한다.
- Kakao SDK의 `libraries=clusterer`를 실제로 사용한다.
- 지도, marker, clusterer instance는 `useRef`로 관리하고 React render마다 지도 전체를 재생성하지 않는다.
- 날짜 표시는 ISO 문자열 대신 `YYYY.MM.DD`로 통일한다.
- 모든 CTA는 아이콘 또는 icon+text button으로 통일한다.

## 변경하지 말 것

- `/api/v1/places`의 기존 계약을 breaking change로 바꾸지 않는다.
- 개인 실명 마스킹 정책을 표시 단계로 미루지 않는다.
- 공공누리 출처 표시를 제거하지 않는다.
- 댓글·평점·후기·커뮤니티 기능을 이번 리터치 PR에 끼워 넣지 않는다. 이는 영구 금지가 아니라 별도 정책 결정과 법무 문서 업데이트가 필요한 범위 분리다.
- 레퍼런스 서비스의 침습적 광고 배치, 커뮤니티 랭킹 게임화, 신고 경쟁 기능을 그대로 복제하지 않는다.

## 수익화 방향

- 광고는 허용 가능한 수익화 수단이다.
- 홈 지도에는 작은 `AdSlot` 또는 후원 배너 영역을 둘 수 있지만, 기본 구현은 환경변수나 설정값이 없으면 렌더링하지 않는 구조로 둔다.
- 광고는 source pill, 신고 CTA, 원문 링크, 지도 컨트롤을 가리면 안 된다.
- 광고 문구는 공공데이터 출처나 등급 산식과 혼동되지 않게 "광고" 또는 "후원" 라벨을 명확히 표시한다.

## 현재 구현에서 반드시 고칠 점

- `apps/web/src/App.tsx`의 `loadPlaces()`가 첫 번째 식당을 자동 선택하는 동작을 제거한다.
- `apps/web/src/styles.css`의 `.app-main` 3열 grid를 full-bleed map 기반 레이어 구조로 교체한다.
- 홈 화면의 `.site-footer`가 `height: calc(100vh - 64px - 74px)` 계산에 들어가는 구조를 없앤다.
- `MapCanvas`에서 map과 overlay를 effect마다 새로 만들지 말고, map/markers/clusterer를 ref로 보관한다.
- 카카오 SDK는 이미 `libraries=clusterer`를 로드하지만, 실제 `MarkerClusterer` instance를 생성해 사용해야 한다.
