# 03. 정보 구조

## 목적

리터치 후 홈 화면의 레이어 구조, 데스크탑·모바일 IA, 상태 전이를 정의한다.

## 읽는 대상

- 프론트엔드 구현자
- UI QA 담당자
- 접근성 QA 담당자

## 완료 기준

- 홈은 full-bleed map 위에 필요한 UI layer만 얹는 구조로 구현된다.
- 데스크탑과 모바일의 UI 배치가 명확히 분리된다.
- 초기 진입, 필터 결과 없음, marker 선택, detail 닫기, URL 복구 상태가 모두 정의된다.

## 라우트 구조

기존 라우트는 유지한다.

| 경로 | 역할 | 리터치 영향 |
|---|---|---|
| `/` | 홈 지도 | 리터치 대상 |
| `/r/{slug}-{place_id}` | 식당 상세 딥링크용 SPA 라우트 | v1.1 이상에서 query 기반 선택과 병행 검토 |
| `/agency/{agency_id}` | 기관 페이지 | 이번 리터치 범위 밖 |
| `/about` | 서비스 소개 | footer 유지 |
| `/privacy` | 개인정보처리방침 | footer 유지 |
| `/terms` | 이용약관 | footer 유지 |
| `/disclaimer` | 면책조항 | footer 유지 |
| `/legal` | 데이터 출처·공공누리 안내 | footer 유지 |
| `/api` | 공개 API 문서 | footer 유지 |

## 홈 화면 레이어

홈은 다음 layer로 구성한다.

| Layer | 역할 | 데스크탑 | 모바일 |
|---|---|---|---|
| MapCanvas | Kakao map, marker, cluster | full viewport | full viewport |
| FloatingSearchFilter | 검색, 자치구, 등급, 정렬 | 좌상단 floating bar | 상단 compact search 또는 sheet 내부 |
| PlaceListSheet | 검색·필터 결과 목록 | 좌측 floating sheet 또는 접힘 panel | bottom sheet list tab |
| PlaceDetails | 식당 상세 | 우측 drawer | bottom sheet detail tab |
| SourcePill | 공공누리 출처, 문서 링크 | 좌하단 또는 우하단 small pill | bottom nav 위 small pill |
| BottomNav | 주요 모드 전환 | 없음 | 지도·목록·필터·정보 |
| ReportModals | 폐업 신고, 수정·삭제 요청 | modal | modal 또는 sheet modal |

## 데스크탑 IA

기준: `min-width: 768px`

```
┌─────────────────────────────────────────────────────────────┐
│ [공무원맵] [검색........] [자치구] [등급] [정렬]       [정보] │ floating top bar
│                                                             │
│   ┌───────────────┐                         ┌────────────┐  │
│   │ 목록 sheet     │                         │ detail      │  │
│   │ 검색 결과      │          지도            │ drawer      │  │
│   │ 정렬/row       │                         │ 선택 시 표시 │  │
│   └───────────────┘                         └────────────┘  │
│                                                             │
│ [공공누리 제1유형 · 서울특별시 정보소통광장 외]              │ source pill
└─────────────────────────────────────────────────────────────┘
```

### 데스크탑 규칙

- top bar는 지도 위에 floating으로 배치한다.
- detail drawer는 식당 선택 시에만 열린다.
- 선택된 식당이 없으면 detail drawer를 렌더링하지 않는다.
- 목록 sheet는 검색어가 있거나 사용자가 목록 버튼을 눌렀을 때 열린다.
- 지도를 클릭하면 marker 선택은 해제할 수 있다. 단, 필터나 sheet 클릭은 해제로 처리하지 않는다.
- source pill은 항상 보이되 지도 컨트롤과 겹치지 않는다.

## 모바일 IA

기준: `max-width: 767px`

```
┌──────────────────────┐
│ compact search       │
│                      │
│       지도           │
│                      │
│ [source pill]        │
├──────────────────────┤
│ bottom sheet          │ peek/mid/full
├──────────────────────┤
│ 지도  목록  필터  정보 │ bottom nav
└──────────────────────┘
```

### 모바일 규칙

- bottom nav는 safe-area inset을 반영한다.
- bottom sheet는 `peek`, `mid`, `full` 상태를 가진다.
- marker 선택 시 bottom sheet는 detail tab으로 열리고 최소 `mid` 높이가 된다.
- 목록 tab에서는 검색 결과와 정렬 control을 제공한다.
- 필터 tab에서는 자치구, 등급, 폐업 포함을 조작한다.
- 기관 유형 필터는 기존 `docs/UI_UX.md`에 남아 있지만, 이번 리터치의 URL 동기화 대상은 아니다. 데이터·API 준비가 끝난 뒤 v1.1에서 별도 query로 추가한다.
- 정보 tab에서는 공공누리 출처, 면책 링크, API 링크를 제공한다.
- detail sheet를 아래로 닫으면 `place` query를 제거하고 선택을 해제한다.

## 상태 모델

| 상태 | 조건 | UI |
|---|---|---|
| `initial` | `/` 진입, query 없음 | 서울 전체 지도, 기본 필터, 선택 없음 |
| `loading` | API 요청 중 | map skeleton 또는 기존 map 유지 + loading indicator |
| `ready_unselected` | 데이터 로드 완료, 선택 없음 | marker/cluster만 표시, detail 닫힘 |
| `ready_selected` | `place` query 또는 marker/list 선택 | detail drawer/sheet 열림 |
| `empty_filtered` | 필터 결과 0건 | 지도 유지, 목록/sheet에 빈 상태와 필터 리셋 버튼 |
| `error` | API 실패 | toast 또는 sheet 내 오류, 재시도 button |
| `reporting` | 신고/수정 모달 열림 | focus trap modal |

## 초기 상태

초기 진입 시 `selectedPlace` 자동 선택은 금지한다.

- 허용: `?place={place_id}`가 있는 경우 해당 place를 찾아 선택한다.
- 허용: `/r/{slug}-{place_id}` 딥링크로 들어온 경우 해당 place를 선택한다.
- 금지: places 배열의 첫 번째 항목을 자동 선택한다.

## URL query 상태

| Query | 값 | 예시 |
|---|---|---|
| `q` | 검색어 | `?q=스타벅스` |
| `region` | 자치구 또는 지역명, comma-separated | `?region=서울%20강남구,서울%20중구` |
| `grade` | 등급, comma-separated | `?grade=★★★,★★` |
| `sort` | `score`, `recent`, `visits` | `?sort=recent` |
| `place` | place id | `?place=8c5e2f3a-...` |

## 상태 전이

| 사용자 행동 | 이전 상태 | 다음 상태 |
|---|---|---|
| `/` 진입 | 없음 | `initial` → `loading` → `ready_unselected` |
| query 포함 진입 | 없음 | `loading` → query 복구 → 필요 시 `ready_selected` |
| 검색 입력 | any | URL `q` 갱신, 목록 sheet 열림 |
| 자치구 선택 | any | URL `region` 갱신, marker/cluster 갱신 |
| 등급 변경 | any | URL `grade` 갱신, marker/cluster 갱신 |
| 정렬 변경 | any | URL `sort` 갱신, 목록 순서 변경 |
| cluster 클릭 | ready | 지도 확대, 선택 없음 |
| marker 클릭 | ready | `place` query 갱신, detail 열림 |
| list row 클릭 | ready | `place` query 갱신, 지도 pan, detail 열림 |
| detail 닫기 | selected | `place` query 제거, 선택 없음 |
| 지도 빈 영역 클릭 | selected | 선택 해제 가능 |
| 신고 접수 완료 | reporting | modal 완료 상태, 필요 시 데이터 재조회 |

## 정적 문서 IA

정적 문서 페이지는 홈 리터치의 full-bleed 구조를 사용하지 않는다.

- `/about`, `/privacy`, `/terms`, `/disclaimer`, `/legal`, `/api`는 기존 문서형 레이아웃을 유지한다.
- 정적 문서 footer는 운영자 정보, 공공누리 출처, 문서 링크를 계속 표시한다.
- 홈 source pill은 정적 문서 footer를 대체하지 않는다.
