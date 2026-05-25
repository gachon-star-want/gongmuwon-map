# 07. 구현 계획

## 목적

UI/UX 리터치를 실제 코드로 옮길 때의 작업 순서, 컴포넌트 분리, 수정 지점을 정의한다.

## 읽는 대상

- 프론트엔드 구현자
- API route 구현자
- 코드 리뷰어

## 완료 기준

- 기존 3열 grid를 제거하고 full-bleed map 레이어 구조로 전환한다.
- Kakao map, marker, clusterer instance를 `useRef`로 관리한다.
- 신규 UI API를 추가하되 기존 `/api/v1/places`는 breaking change 없이 유지한다.

## 사전 확인

구현 전 다음 문서를 읽는다.

- `docs/PRD.md`
- `docs/UI_UX.md`
- `docs/LEGAL_PRIVACY.md`
- `docs/PUBLIC_API.md`
- 이 폴더의 `01`부터 `06`까지 문서

## 권장 파일 구조

현재는 `apps/web/src/App.tsx`에 대부분의 UI가 모여 있다. 리터치 구현 시 다음처럼 분리한다.

```text
apps/web/src/
  App.tsx
  styles.css
  features/map/
    MapExperience.tsx
    MapCanvas.tsx
    FloatingSearchFilter.tsx
    PlaceListSheet.tsx
    PlaceDetails.tsx
    SourcePill.tsx
    AdSlot.tsx
    BottomNav.tsx
    ReportModals.tsx
    hooks/
      useKakaoMap.ts
      usePlacesSearch.ts
      useUrlQueryState.ts
      useResponsiveMode.ts
    types.ts
    format.ts
```

작업량을 줄여야 하면 한 번에 완전 분리하지 않아도 된다. 단, `MapCanvas`와 URL query state는 반드시 독립된 단위로 관리한다.

## API 구현 순서

1. `api/v1/places/search.ts`를 추가한다.
2. `api/v1/regions.ts`를 추가한다.
3. `apps/web/public/openapi.json`에 신규 endpoint를 추가한다.
4. `apps/web/public/llms.txt`, `apps/web/public/llms-full.txt`에 신규 endpoint와 출처 표시를 추가한다.
5. 기존 `api/v1/places.ts`의 query와 응답 필드는 변경하지 않는다.

## 프론트엔드 구현 순서

### 1. 타입과 formatter 정리

- `Place`, `Visit`, `Region`, `SearchResponse` 타입을 분리한다.
- `formatDate(dateString)`은 `YYYY-MM-DD`를 `YYYY.MM.DD`로 표시한다.
- `formatMoney`, `formatVisitCount`, `gradeLabel`, `gradeClass`를 공용 formatter로 둔다.

### 2. URL query state 도입

- `q`, `region`, `grade`, `sort`, `place`를 URL query와 동기화한다.
- 초기 진입 시 query를 먼저 파싱한다.
- query가 없으면 `selectedPlace`는 `null`이다.
- `loadPlaces()` 또는 검색 결과 로드 후 `data[0]`을 자동 선택하지 않는다.

### 3. 데이터 fetching 분리

- 지도 marker용 데이터와 검색 결과 목록용 데이터를 구분한다.
- 지도 marker는 bbox 또는 현재 visible bounds 기준으로 `/api/v1/places`를 사용할 수 있다.
- 검색/list는 `/api/v1/places/search`를 사용한다.
- regions filter option은 `/api/v1/regions`를 사용한다.

### 4. MapCanvas 재작성

필수 원칙:

- Kakao script는 `libraries=clusterer&autoload=false`로 유지한다.
- map instance는 `mapInstanceRef`에 저장한다.
- marker instances는 `markersRef`에 저장한다.
- clusterer instance는 `clustererRef`에 저장한다.
- React render마다 `new kakao.maps.Map(...)`을 호출하지 않는다.
- 필터 결과가 바뀌면 marker set만 diff 또는 clear/add한다.
- selected marker style은 overlay 재생성이 아니라 class/state update로 처리한다.

구현 체크:

- 최초 mount 때 map 생성
- SDK ready 후 clusterer 생성
- places 변경 시 marker 업데이트
- clusterer에 marker 등록
- cluster click 시 zoom/pan
- marker click 시 `onSelect(place)` 호출
- unmount 시 marker와 listener 정리

### 5. 레이아웃 CSS 교체

수정 대상:

- `apps/web/src/styles.css`
- `.app-main`
- `.control-panel`
- `.detail-panel`
- `.site-footer`
- `.map-surface`

방향:

- `.app-main`은 grid가 아니라 full viewport relative container가 된다.
- 홈 footer는 제거하고 `SourcePill` component로 대체한다.
- 정적 문서 페이지의 `.static-footer`는 유지한다.
- desktop layer와 mobile layer를 breakpoint로 분리한다.

### 6. 데스크탑 UI 구현

- `FloatingSearchFilter`
- `PlaceListSheet`
- `PlaceDetails` right drawer
- `SourcePill`

동작:

- 선택 없음: drawer 닫힘
- marker/list 선택: drawer 열림
- 검색어 있음: list sheet 열림
- Escape: drawer 또는 sheet 닫힘

### 7. 모바일 UI 구현

- `BottomNav`
- `BottomSheet`
- sheet tab: list, detail, filter, info

동작:

- marker 선택: detail tab, mid height
- 목록 버튼: list tab, mid height
- 필터 버튼: filter tab, full 또는 mid height
- 정보 버튼: info tab, mid height
- sheet dismiss: 선택 해제 또는 tab 닫기

### 8. 상세와 신고 모달 정리

- `PlaceDetails`는 desktop drawer와 mobile sheet에서 같은 콘텐츠를 사용한다.
- CTA는 icon+text button으로 통일한다.
- 폐업 신고와 정보 수정·삭제 요청은 `ReportModals`로 분리한다.
- 정보 수정·삭제 요청의 자유 텍스트 최소 길이는 50자다.
- 제출 성공 시 현재 목록에서 해당 식당을 숨기거나 재조회한다.

### 9. 광고 수익화 slot 준비

- `AdSlot` component를 optional로 만든다.
- 광고 설정값이나 env가 없으면 아무것도 렌더링하지 않는다.
- desktop은 list sheet 하단 또는 detail drawer 하단에만 배치한다.
- mobile은 bottom sheet 내부 하단에만 배치한다.
- 지도 위 고정 대형 banner는 source pill, bottom nav, 지도 조작을 방해하므로 구현하지 않는다.
- 광고 label은 `광고` 또는 `후원`으로 명확히 표시한다.

### 10. 정적 문서 페이지 회귀 방지

- `StaticPage`의 footer는 유지한다.
- `/about`, `/privacy`, `/terms`, `/disclaimer`, `/legal`, `/api` 경로가 계속 렌더링되는지 확인한다.
- 홈의 `SourcePill`과 정적 footer의 역할을 섞지 않는다.

## 현재 코드에서 직접 고칠 지점

### `apps/web/src/App.tsx`

- `loadPlaces()`의 `setSelectedPlace((current) => current ?? data[0] ?? null)` 제거.
- `MapExperience`의 local state를 URL query 기반 state로 교체.
- `MapCanvas`의 effect 안 map 재생성 로직 제거.
- `PlaceDetails`의 날짜 표시를 formatter로 교체.
- CTA button에 lucide icon을 추가한다.

### `apps/web/src/styles.css`

- `.app-main` 3열 grid 제거.
- `.control-panel`, `.detail-panel` 고정 column 스타일 제거.
- `.site-footer`가 홈 높이 계산에 들어가는 구조 제거.
- `.source-pill`, `.floating-search`, `.list-sheet`, `.detail-drawer`, `.bottom-nav`, `.bottom-sheet` 스타일 추가.

### `api/`

- `api/v1/places.ts` 유지.
- `api/v1/places/search.ts` 추가.
- `api/v1/regions.ts` 추가 또는 기존 `api/v1/agencies.ts`와 충돌 없이 별도 route 추가.

## 구현 중 범위 밖인 사항

- 댓글·평점·후기·커뮤니티 필드 추가. 도입하려면 ADR과 법무 문서 업데이트부터 별도 PR로 진행한다.
- 레퍼런스의 침습적 광고 영역을 그대로 복제
- 첫 결과 자동 선택
- `/api/v1/places` 기존 응답 타입 변경
- 지도 instance를 render/effect마다 새로 생성
- footer 출처 표시 제거
- 정적 문서 페이지 footer 삭제

## 코드 리뷰 체크포인트

- URL query가 source of truth인지 확인한다.
- `selectedPlace` 초기값이 `null`인지 확인한다.
- `MapCanvas`가 ref 기반으로 map/clusterer를 유지하는지 확인한다.
- marker 수가 늘어도 전체 map 재생성이 없는지 확인한다.
- mobile safe-area가 bottom nav와 sheet에 반영됐는지 확인한다.
- 출처 표시가 홈과 정적 문서 모두에 남아 있는지 확인한다.
