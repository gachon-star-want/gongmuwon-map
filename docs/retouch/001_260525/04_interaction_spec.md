# 04. 인터랙션 사양

## 목적

검색, 필터, 자치구 선택, 목록 정렬, 마커 선택, 상세 열기/닫기, 신고 모달, URL 동기화의 동작을 구체화한다.

## 읽는 대상

- 프론트엔드 구현자
- API 구현자
- QA 담당자

## 완료 기준

- 모든 주요 사용자 행동의 입력, 상태 변경, URL 변경, 화면 결과가 정의된다.
- 뒤로가기·새로고침·공유 링크가 같은 상태를 복구한다.
- 초기 진입 시 식당이 자동 선택되지 않는다.

## 검색

### 입력

- 검색 대상: 식당명, 주소, 카테고리, 부서명.
- 입력 필드 placeholder: `식당명, 자치구, 부서 검색`.
- 입력 변경 후 250ms debounce를 적용한다.
- 검색어가 비어 있으면 `q` query를 제거한다.

### 결과

- 검색어가 있으면 list sheet를 연다.
- 결과는 `/api/v1/places/search?q={q}`에서 가져온다.
- 식당명을 우선 매칭하고, 주소·부서명 매칭은 보조로 취급한다.
- 검색 결과 row 클릭 시:
  - `place` query를 설정한다.
  - 지도를 해당 좌표로 pan한다.
  - desktop은 right drawer를 연다.
  - mobile은 bottom sheet detail tab을 연다.

### 빈 결과

- 문구: `조건에 맞는 식당이 없습니다.`
- CTA: `필터 초기화`
- CTA는 icon+text button으로 만든다.

## 자치구 선택

- 다중 선택 가능하다.
- 기본값은 전체다.
- 선택 값은 `region` query에 comma-separated로 저장한다.
- 값은 표시명 축약 없이 API와 동일한 정식 값으로 저장한다. 예: `서울 강남구`.
- chip에서는 `강남구`처럼 짧게 표시할 수 있다.
- 모든 자치구를 해제하면 `region` query를 제거한다.

## 등급 필터

기본값:

- `★★★` on
- `★★` on
- `✦` on
- `★` off
- 폐업 포함 off

규칙:

- 선택된 등급은 `grade` query에 comma-separated로 저장한다.
- 등급을 모두 끄는 상태는 허용하지 않는다. 마지막 등급을 끄려고 하면 기존 상태를 유지한다.
- 폐업 포함은 별도 UI 상태로 두되, v1 query에는 넣지 않는다. 필요 시 v1.1에서 `closed=1`을 추가한다.

## 목록 정렬

| sort 값 | 라벨 | 기준 |
|---|---|---|
| `score` | 추천순 | score desc, last_visit_at desc |
| `recent` | 최근 방문순 | last_visit_at desc |
| `visits` | 방문 많은순 | visit_count_12m desc, unique_department_count_12m desc |

- 기본값은 `score`다.
- 기본값일 때는 `sort` query를 생략할 수 있다.
- 정렬 변경은 marker 표시 여부를 바꾸지 않고 목록 순서만 바꾼다.

## 마커와 클러스터

### 클러스터

- 낮은 줌에서는 개별 마커보다 클러스터를 우선 표시한다.
- 클러스터 클릭 시 한 단계 이상 확대하고 해당 클러스터 중심으로 pan한다.
- 클러스터는 내부 식당 수를 표시한다.
- 클러스터 색상은 내부 식당 중 가장 높은 등급을 기준으로 한다.
- 클러스터 클릭만으로 `place` query를 설정하지 않는다.

### 개별 마커

- marker 클릭 시 해당 식당을 선택한다.
- 선택 시 URL `place` query를 설정한다.
- 선택된 marker는 크기, outline, z-index로 구분한다.
- marker hover/focus 시 식당명 tooltip을 표시한다.
- marker의 accessible name은 `"{등급 라벨}, {식당명}, {자치구}"` 형식으로 한다.

## 상세 열기와 닫기

### 열기

다음 행동은 상세를 연다.

- marker 클릭
- list row 클릭
- URL에 `place` query가 있는 상태로 진입
- `/r/{slug}-{place_id}` 딥링크 진입

### 닫기

다음 행동은 상세를 닫고 선택을 해제한다.

- drawer/sheet 닫기 버튼 클릭
- 모바일 sheet를 peek 아래로 dismiss
- 지도 빈 영역 클릭
- Escape key

닫기 시 `place` query를 제거한다. `q`, `region`, `grade`, `sort`는 유지한다.

## 상세 콘텐츠

상세에는 다음 순서를 사용한다.

1. 등급 badge, 폐업 제보 badge
2. 식당명, 주소
3. 자치구 백분위 설명
4. 방문 횟수, 부서 수, 최근 방문일, 평균 인당 금액
5. 방문 부서 요약
6. 방문 기록 목록
7. 카카오맵에서 보기
8. 원문 링크
9. 폐업 신고
10. 정보 수정·삭제 요청

날짜는 모두 `YYYY.MM.DD`로 표시한다.

## 폐업 신고 모달

- CTA 라벨: `폐업 신고`
- 사유 선택:
  - `방문해보니 폐업`
  - `다른 가게 입점`
  - `장기 휴업`
- 제출 시 `reporter_fp`를 포함한다.
- 같은 브라우저의 중복 신고는 서버에서 차단한다.
- 제출 성공 문구: `접수되었습니다. 방문 전 확인 안내에 반영됩니다.`
- 누적 1~2건이면 detail 상단에 `폐업 제보 N건 - 방문 전 확인 권장` 배너를 표시한다.
- 누적 3건 이상이면 폐업 라벨과 흐린 marker를 표시한다.

## 정보 수정·삭제 요청 모달

- CTA 라벨: `정보 수정·삭제 요청`
- 안내 문구: `접수 즉시 임시 비공개 처리 후 72시간 내 검토합니다.`
- 사유 radio:
  - `식당 정보 오류`
  - `방문 기록 오류`
  - `본인·소속 정보 노출 우려`
  - `기타`
- 자유 텍스트는 필수이며 50자 이상이다.
- 이메일은 선택이지만, 회신을 원하면 입력하도록 안내한다.
- 제출 성공 후 해당 식당은 현재 화면에서 숨긴다.

## URL query 동기화

### 읽기

초기 render에서 URL query를 파싱한다.

- `q`: 검색어 state
- `region`: 자치구 배열
- `grade`: 등급 배열
- `sort`: 정렬
- `place`: 선택 식당 id

잘못된 값은 무시하고 기본값으로 복구한다.

### 쓰기

- 사용자 입력으로 state가 바뀌면 URL query를 갱신한다.
- 검색 입력 중에는 `replaceState`를 사용해 history를 과도하게 늘리지 않는다.
- marker/list 선택, detail 닫기, 필터 확정은 `pushState`를 사용한다.
- browser back/forward는 state를 복구한다.

### 예시

```
/?q=스타벅스&region=서울%20강남구&grade=★★★,★★&sort=recent&place=8c5e2f3a-...
```

## 접근성 인터랙션

- Tab 순서: 검색 → 필터 → 목록 → 지도 marker → 상세 drawer → source pill.
- Escape는 열린 최상위 layer부터 닫는다.
- sheet/drawer open 상태에서는 focus가 새 layer 안으로 이동한다.
- 모달 open 상태에서는 focus trap을 유지한다.
- icon-only button은 tooltip과 `aria-label`을 모두 가진다.
