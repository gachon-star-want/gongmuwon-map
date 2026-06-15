# ADR-019: 거주적합도 POI 근거(표시 전용)와 점수 분리

- 상태: 채택 (2026-06-15)
- 관련: [ADR-015](ADR-015-livability-score-formula.md)(점수 공식), [ADR-016](ADR-016-livability-spatial-data.md)(공간데이터), [ADR-018](ADR-018-livability-reason-summary-and-why-as-map.md)(요약·Why-as-Map)

## Context

「살기 좋은 동네」 상세는 분야 percentile로 강점/약점을 보여주지만(ADR-018), 그 근거가 추상적이다("교육·보육이 좋아요"). 사용자는 **"무엇이 있어서"** 살기 좋은지 구체 시설(POI)을 원했다(예: "동네 안에 초등학교 3곳, 어린이집 12곳"). 단, 다음 제약이 있다.

- **점수 오염 금지**: POI를 점수에 가산하면 "시설 많음=좋은 동네" 단순화 + 중복 계산이 된다. 점수는 이미 SGIS 지표로 산출(ADR-015). POI는 **근거 표시 전용**이어야 한다.
- **데이터 획득 제약(Phase 0 실측)**: `localdata.go.kr`은 현재 네트워크에서 차단(timeout), `data.go.kr` 파일 다운로드(`FileDown.do`)는 헤드리스/curl에 0바이트(봇차단). **`data.go.kr` 인증키(serviceKey) 기반 OpenAPI(`apis.data.go.kr`/`odcloud`)만 자동화 가능**(SGIS/KOSIS와 동일 패턴).
- **좌표계 혼재**: 학교/어린이집 표준데이터는 WGS84 경위도(변환 불필요), LocalData 인허가는 중부원점 TM(EPSG:5174, Bessel) → WGS84 재투영 필수.
- **공간 정밀도 한계**: 읍면동 경계가 작아 시설이 0인 경우가 흔하고(중·고교/대형마트), 인허가 누락(편의점/슈퍼)도 크다. 0을 약점으로 표시하면 낙인(ADR-015 "결측 0점 금지" 위배).

## Decision

### 1. 점수와 물리적 분리 (가장 중요)
POI는 점수 파이프라인과 **별도 테이블**에만 저장한다. `metric_catalog`/`neighborhood_metrics`에 **절대 넣지 않는다** — 거기 들어가면 `neighborhood_scores_v1`/`neighborhood_field_scores_v1` MV에 자동 편입되어 점수를 오염시킨다.

- `poi_type_catalog(poi_type PK, category, display_name, source_id, source_notice)` — POI 유형 메타 + 출처
- `neighborhood_poi_counts(adm_cd, poi_type, distance_basis, ref_period, count, ...)` — 읍면동별 카운트
- 점수 MV는 이 테이블을 **JOIN하지 않는다**. CI 가드로 점수 MV SQL에 `neighborhood_poi_counts`/`poi_` 등장 시 빌드 실패시킨다.

### 2. 공간 환산 — 오프라인 PIP 기본, 직선버퍼는 보조
ADR-016대로 런타임 공간조인 금지, Python 오프라인 사전계산(shapely).

- **기본 = point-in-polygon**: `region_boundaries`(WGS84) 경계 내 POI 카운트. `distance_basis='pip'`. 카피 "동네 안에 N곳".
- **보조 = 직선버퍼 1km**: 경계 내 0인 광역시설(중·고교/대형마트)만, 읍면동 중심점 반경 1km 직선거리. `distance_basis='buffer_1km_straight'`. 카피 "도보권(직선거리 추정) N곳". **PIP와 합산 금지**, "직선거리 추정"임을 라벨로 강제(실제 도보경로 아님).

### 3. 좌표·품질 게이트
- 학교/어린이집 = WGS84 그대로. LocalData = `EPSG:5174→4326`(pyproj, datum-shift) 변환.
- 변환 후 한국 bbox(위도 33~39, 경도 124~132) 밖·0·결측 좌표는 스킵.
- LocalData는 `영업상태명='영업/정상'`만 적재(폐업/휴업 제외).

### 4. 표시 정책 (낙인 방지)
- **강점 분야에만** POI 근거를 노출한다(ADR-018 강점 칩 옆). 약점/0 카운트는 표시하지 않는다.
- "점수에는 반영되지 않은 참고 정보" 문구 + 출처(공공누리) 명시.

### 5. 데이터 획득
`data.go.kr` serviceKey(`DATA_GO_KR_SERVICE_KEY`) 기반 OpenAPI. 데이터셋: 학교 `15021148`, 어린이집 `15013108`, 의료기관/약국(welfare). LocalData 직접 다운로드는 차단되어 채택하지 않는다.

## Consequences

- 점수와 POI가 독립 → POI 추가/오류가 점수에 영향 없음, ADR-015/018 일관.
- POI는 "왜 살기 좋은지"의 구체 근거를 제공하되 가중치 논쟁에서 자유롭다.
- 단계: Phase 1 education(학교+어린이집, WGS84·PIP) → Phase 2 welfare/convenience(LocalData, EPSG:5174 변환) → Phase 3 직선버퍼 보조.
- convenience(편의점/마트)는 인허가 누락이 커 과소집계 가능 → "참고" 한계 명시.
- 비용: serviceKey OpenAPI는 무료(트래픽 제한 내), 월배치 1회.
