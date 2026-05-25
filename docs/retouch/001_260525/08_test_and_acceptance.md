# 08. 테스트와 인수 기준

## 목적

UI/UX 리터치 구현 후 빌드, API, desktop/mobile QA, 접근성, 회귀 검증 기준을 정의한다.

## 읽는 대상

- 구현자
- QA 담당자
- 코드 리뷰어
- 배포 담당자

## 완료 기준

- 아래 체크리스트를 통과해야 리터치 구현을 완료로 본다.
- 공공누리 출처 표시, 이번 리터치 범위 밖인 댓글·평점·후기 미도입, 광고 slot의 비침습성을 회귀 검증한다.
- desktop과 mobile에서 주요 floating UI가 겹치지 않는다.

## 필수 명령

프론트엔드 빌드:

```bash
npm run build
```

보안 감사:

```bash
npm audit --omit=dev --json
```

실행 위치는 실제 package script가 있는 디렉터리를 기준으로 한다. 현재 웹 앱 기준으로는 `apps/web`에서 실행한다.

## API smoke

로컬 또는 배포 preview에서 다음 요청이 성공해야 한다.

```text
GET /api/v1/places/search?q=스타벅스&limit=20
GET /api/v1/places/search?region=서울 강남구&grade=★★★
GET /api/v1/places/search?region=서울%20강남구&grade=★★★
GET /api/v1/regions
```

두 번째 줄은 계획서와 같은 가독성 표기이고, 실제 요청은 세 번째 줄처럼 URL 인코딩된 값으로 보낸다.

확인 항목:

- HTTP 200
- JSON parse 가능
- `items` 배열 존재
- `source_notice` 존재
- 날짜 field는 API에서 `YYYY-MM-DD`이며 UI에서 `YYYY.MM.DD`로 표시
- 댓글·평점·후기 관련 field 없음. 이번 리터치 API 범위가 아니기 때문이다.

## Desktop QA

### Viewport

- 1440px width
- 1976px width

### 확인 항목

- 첫 진입 시 selected place가 없다.
- 지도는 viewport 전체를 채운다.
- 기존 3열 grid가 보이지 않는다.
- floating search/filter가 지도 컨트롤과 겹치지 않는다.
- list sheet와 right drawer가 서로 겹치지 않는다.
- source pill이 지도 조작 버튼, drawer, sheet와 겹치지 않는다.
- drawer 닫기 시 `place` query가 제거된다.
- search/filter/detail/source pill 텍스트가 부모 밖으로 넘치지 않는다.
- 정적 문서 footer는 `/about`, `/privacy`, `/terms`, `/disclaimer`, `/legal`, `/api`에서 유지된다.

## 클러스터 QA

- 서울 전체 줌에서 개별 marker보다 cluster가 우선 보인다.
- cluster label은 식당 수를 표시한다.
- cluster 클릭 시 확대 또는 pan이 동작한다.
- 확대 후 개별 marker가 표시된다.
- marker 클릭 시 detail drawer/sheet가 열린다.
- marker 선택은 `place` query에 반영된다.
- 필터 변경 시 map instance가 재생성되는 깜빡임이 없어야 한다.

## Mobile QA

### Viewport

- 390x844
- 430x932

### 확인 항목

- bottom nav가 safe-area를 침범하지 않는다.
- bottom sheet peek/mid/full 상태가 동작한다.
- compact search와 source pill이 서로 겹치지 않는다.
- marker 선택 → 상세 sheet → 원문 링크 → 신고 버튼 플로우가 가능하다.
- detail sheet 닫기 시 `place` query가 제거된다.
- 필터 tab에서 자치구와 등급을 조작할 수 있다.
- list tab에서 정렬 변경이 가능하다.
- sheet full 상태에서도 CTA가 bottom nav에 가려지지 않는다.

## URL 회귀 테스트

다음 URL로 직접 진입해 상태가 복구되는지 확인한다.

```text
/?q=스타벅스
/?region=서울%20강남구&grade=★★★,★★
/?sort=recent
/?q=스타벅스&region=서울%20강남구&grade=★★★&sort=visits
/?place={known_place_id}
```

확인 항목:

- query 없는 `/`는 선택 없음
- `place` query가 있을 때만 detail 열림
- 잘못된 `grade`나 `sort`는 무시되고 기본값으로 복구
- browser back/forward가 UI state를 복구

## 접근성 QA

- Tab으로 검색, 필터, 목록, marker, 상세, source pill에 도달 가능하다.
- Escape가 열린 drawer/sheet/modal을 닫는다.
- icon-only button에는 `aria-label`이 있다.
- marker에는 등급, 식당명, 자치구가 포함된 accessible name이 있다.
- 모달은 focus trap을 유지한다.
- 색 대비는 일반 텍스트 4.5:1 이상이다.
- `prefers-reduced-motion`에서 drawer/sheet motion이 줄어든다.

## 법적·정책 회귀

- 사용자 댓글·평점·후기 UI가 이번 리터치 PR에 섞여 있지 않다.
- API 응답에 댓글·평점·후기 field가 없다.
- 공공누리 제1유형 출처가 home source pill에 있다.
- 공공누리 제1유형 출처가 정적 문서 footer에 있다.
- 공공누리 제1유형 출처가 OpenAPI와 `llms.txt`에 있다.
- 정보 수정·삭제 요청 문구에 72시간 검토와 즉시 임시 비공개 원칙이 남아 있다.
- 공무원 비위·부정행위 단정 문구가 없다.
- 광고 slot을 구현했다면 "광고" 또는 "후원" label이 있고, source pill·지도 컨트롤·신고 CTA·원문 링크와 겹치지 않는다.

## 정적 페이지 회귀

다음 경로가 유지되어야 한다.

- `/about`
- `/privacy`
- `/terms`
- `/disclaimer`
- `/legal`
- `/api`
- `/llms.txt`
- `/llms-full.txt`
- `/openapi.json`

확인 항목:

- 각 페이지가 404가 아니다.
- footer가 표시된다.
- 운영자 정보와 출처 정보가 표시된다.
- 홈 전용 source pill이 정적 문서 footer를 대체하지 않는다.

## 인수 체크리스트

- [ ] 기존 3열 grid 제거
- [ ] full-bleed map 적용
- [ ] 초기 자동 선택 제거
- [ ] Kakao clusterer 실제 사용
- [ ] map/marker/clusterer ref 관리
- [ ] URL query 동기화
- [ ] desktop floating search/filter 적용
- [ ] desktop right drawer 적용
- [ ] mobile bottom nav 적용
- [ ] mobile bottom sheet 적용
- [ ] home source pill 적용
- [ ] static footer 유지
- [ ] `/api/v1/places/search` 추가
- [ ] `/api/v1/regions` 추가
- [ ] `/api/v1/places` breaking change 없음
- [ ] 날짜 `YYYY.MM.DD` 표시
- [ ] icon 또는 icon+text CTA 적용
- [ ] 댓글·평점·후기 미도입. 이번 리터치 범위가 아니므로 별도 ADR 전까지 섞지 않음
- [ ] 광고 slot이 있다면 비침습적 위치와 label 확인
- [ ] 공공누리 출처 표시 유지
- [ ] `npm run build` 통과
- [ ] `npm audit --omit=dev --json` 결과 검토
