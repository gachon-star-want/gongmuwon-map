# 05. 비주얼 디자인 사양

## 목적

마커, 클러스터, chip, drawer, bottom sheet, typography, spacing, z-index, responsive breakpoint의 시각 기준을 정의한다.

## 읽는 대상

- 프론트엔드 구현자
- 디자인 QA 담당자
- 접근성 QA 담당자

## 완료 기준

- 홈 화면이 지도 우선 서비스처럼 보인다.
- UI 요소끼리 겹치지 않고, desktop/mobile 모두에서 텍스트가 부모 안에 들어간다.
- 기존 3열 grid의 답답한 구조가 제거된다.

## 현재 UI 문제

- 홈이 `control-panel | map | detail-panel` 3열 grid라 지도보다 패널이 먼저 보인다.
- 첫 로드 시 첫 번째 식당이 자동 선택되어 사용자의 의도와 다른 상세 패널이 열린다.
- 홈 footer가 큰 정적 영역으로 남아 지도 높이를 줄인다.
- 모바일에서 control, map, detail이 세로로 쌓여 지도 조작과 상세 확인이 모두 불편하다.
- 날짜가 ISO 문자열로 보일 수 있어 한국어 서비스의 밀도가 떨어진다.
- Kakao clusterer를 로드하지만 실제 cluster UI가 없어 많은 marker 상황을 견디기 어렵다.

## 디자인 원칙

- 지도는 배경 장식이 아니라 주 작업 표면이다.
- 패널은 필요한 정보만 담는 얇은 layer다.
- 카드 안에 카드를 중첩하지 않는다.
- 버튼은 icon 또는 icon+text로 만든다.
- 모서리 radius는 8px 이하를 기본으로 한다.
- 글자 크기는 viewport width로 스케일하지 않는다.
- letter-spacing은 0을 사용한다.
- 한 가지 색조로만 구성된 팔레트를 피하고, 등급 색상은 의미 색으로 제한한다.

## 반응형 breakpoint

| 구간 | 기준 | 레이아웃 |
|---|---|---|
| Mobile | `< 768px` | full map + compact search + bottom nav + bottom sheet |
| Tablet | `768px - 1199px` | full map + floating search/filter + collapsible list + drawer |
| Desktop | `>= 1200px` | full map + floating search/filter + optional list sheet + right drawer |
| Wide desktop | `>= 1760px` | drawer max width 유지, 지도 중심 과도 이동 방지 |

## 레이아웃 치수

### Desktop

- top floating bar: top 16px, left 16px, right auto, max-width 840px
- list sheet: width 360px, max-height `calc(100vh - 136px)`
- right drawer: width 420px, max-width `min(420px, 34vw)`
- source pill: bottom 16px, left 16px 또는 지도 컨트롤과 겹치지 않는 위치
- 지도는 viewport 전체를 채운다.

### Mobile

- compact search: top safe-area + 10px, left/right 12px
- bottom nav: height 64px + safe-area inset
- bottom sheet peek: 112px
- bottom sheet mid: 52vh
- bottom sheet full: `calc(100vh - 72px)`
- source pill: bottom nav 위 8px, 좌우 12px 안에서 한 줄 말줄임

## Z-index

| Layer | z-index |
|---|---|
| Map tiles | 0 |
| Marker | 10 |
| Cluster | 20 |
| Selected marker | 30 |
| Source pill | 80 |
| Floating search/filter | 100 |
| List sheet | 120 |
| Bottom nav | 140 |
| Detail drawer/bottom sheet | 160 |
| Modal overlay | 300 |
| Toast | 350 |

## 색상

### 등급 색상

| 등급 | 색상 | 용도 |
|---|---|---|
| `★★★` 강추 | `#ef4444` | marker, badge, cluster 최고 등급 |
| `★★` 추천 | `#f59e0b` | marker, badge |
| `★` 중립 | `#6b7280` | marker, badge |
| `✦` 신규 | `#3b82f6` | marker, badge |
| 폐업 | 기존 등급색 + opacity 0.35 | marker, row |

### UI 색상

- surface: `#ffffff`
- text primary: `#172033`
- text secondary: `#657386`
- border: `#e2e6ea`
- background tint: `rgba(255,255,255,0.94)`
- focus ring: `#172033`

지도 위 floating surface는 완전 불투명 흰색보다 약간의 투명도를 허용하되, 텍스트 대비는 WCAG AA를 만족해야 한다.

## Typography

| 요소 | 크기 | 굵기 |
|---|---|---|
| App title | 18-20px | 800 |
| Search input | 15-16px | 500 |
| Section heading | 15-17px | 700 |
| Place title in drawer | 22-26px | 800 |
| Row title | 15-16px | 700 |
| Metadata | 12-13px | 500 |
| Source pill | 11-12px | 500 |

## Marker

| 등급 | 크기 | 내용 |
|---|---|---|
| `★★★` | 34px | 별 3개 또는 compact grade |
| `★★` | 30px | 별 2개 |
| `★` | 26px | 별 1개 |
| `✦` | 26px | `NEW` 또는 sparkle |
| selected | +4px 또는 outline | focus ring 포함 |

규칙:

- marker는 흰색 border 2px와 얕은 shadow를 가진다.
- selected marker는 outline과 z-index로만 구분하고 색 의미를 바꾸지 않는다.
- 폐업 marker는 opacity 0.35와 `폐업` tooltip을 사용한다.
- marker text는 부모 안에서 overflow 되지 않아야 한다.

## Cluster

- Kakao `MarkerClusterer`를 실제 사용한다.
- cluster 크기:
  - 2-9개: 36px
  - 10-49개: 44px
  - 50개 이상: 52px
- label은 숫자만 표시한다.
- 색상은 내부 식당 중 최고 등급을 따른다.
- cluster hover/focus 시 outline을 표시한다.
- cluster는 식당 선택 상태를 만들지 않는다.

## Search/filter bar

- search input 높이: 44-48px
- filter chip 높이: 34-36px
- chip selected 상태는 채운 배경과 check icon을 사용한다.
- icon-only 버튼은 40x40px 이상 터치 영역을 확보한다.
- chip 텍스트가 길면 줄바꿈보다 말줄임을 우선한다.

## List sheet

- row 높이: 최소 68px
- row 내용:
  - 등급 badge
  - 식당명
  - 자치구/주소
  - 방문 `N회`
  - 최근 방문 `YYYY.MM.DD`
- active row는 border와 배경 tint로 구분한다.
- 리스트 row를 카드처럼 과하게 띄우지 않는다.

## Detail drawer

- desktop drawer는 오른쪽에서 열린다.
- 너비는 420px 기준, 작은 desktop에서는 34vw 이하로 제한한다.
- drawer 내부는 section divider로 나누고 카드 중첩은 피한다.
- 상단에는 닫기 icon button을 둔다.
- 주요 CTA:
  - `카카오맵에서 보기`
  - `원문 보기`
  - `폐업 신고`
  - `정보 수정·삭제 요청`
- 모든 CTA는 icon+text button으로 통일한다.

## Bottom sheet

- mobile detail과 list는 같은 bottom sheet 안에서 tab으로 전환한다.
- drag handle은 시각적으로 작게, 접근성 이름은 제공한다.
- sheet가 full 상태일 때도 bottom nav와 겹치지 않는다.
- iOS safe-area inset을 반영한다.

## Source pill

홈 source pill 문구:

`공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외`

규칙:

- 홈에서 정적 footer를 대체한다.
- 클릭 시 `/legal`로 이동한다.
- 한 줄 표시를 우선하고, 좁은 화면에서는 말줄임한다.
- 정적 문서 페이지 footer는 별도로 유지한다.

## AdSlot

광고 수익화는 허용한다. 단, 광고는 공공데이터 UI와 명확히 분리한다.

- desktop: list sheet 하단 또는 drawer 하단의 작은 sponsor slot을 우선 검토한다.
- mobile: bottom sheet 내부 list/detail 하단에만 둔다. 지도 하단 고정 banner는 bottom nav와 source pill을 가리기 쉬우므로 기본값으로 쓰지 않는다.
- 광고가 없으면 slot 자체를 렌더링하지 않는다.
- 광고 label은 `광고` 또는 `후원`으로 표시한다.
- 광고는 marker, cluster, source pill, 신고 CTA, 원문 링크와 겹치면 안 된다.

## 날짜와 숫자

- 날짜: `YYYY.MM.DD`
- 금액: `18,300원`
- 방문: `12회`
- 부서: `5개 부서`
- 백분위: `이 자치구 상위 8%`

## 이번 리터치에서 쓰지 않을 시각 패턴

- 댓글/후기 count
- 좋아요/비추천 투표 막대
- 사용자 레벨 badge
- 과도한 hero section
- 지도 위 큰 공지 modal
- 카드 안 카드 중첩
- 텍스트가 버튼 밖으로 넘치는 상태
- 지도 조작을 가리는 대형 광고 banner
