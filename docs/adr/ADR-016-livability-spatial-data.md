# ADR-016 — 거주적합도 공간 데이터: 통계청 코드 단일화 + 오프라인 사전계산

- **Status**: Accepted
- **Date**: 2026-06-14

## Context

거주적합도는 읍면동 폴리곤과, 해상도·좌표계·코드체계가 제각각인 공공데이터(SGIS·KOSIS, 후속 실거래가·범죄·대기질)를 다룬다. 현재 DB는 PostGIS가 아닌 `cube`/`earthdistance`([ADR-010](ADR-010-database-stack-migration.md)). 공간 처리를 어디서 어떻게 할지 결정한다.

## Decision

- **지역코드 단일화 = 통계청 `adm_cd`**. 실측 결과 SGIS와 KOSIS(`DT_1JC1502`)가 동일한 통계청 코드(충북 `33`, 충주 `33020`, 주덕읍 `33020110`)·명칭을 써서 **매핑 테이블 없이 `adm_cd`로 조인**. 행안부 법정동 코드(실거래가)만 Phase 3에서 `adm_code_map`으로 안분.
- **좌표계**: SGIS 경계(`boundary/hadmarea.geojson`)는 UTM-K(EPSG:5179) → 적재 시 **WGS84(4326)로 변환 저장**(pyproj). 주소 지오코딩은 `geocodewgs84` 우선(변환 불필요).
- **공간 환산은 적재(ETL) 단계에서 읍면동으로 사전변환**, 런타임 공간조인 금지. 환산 방식은 `metric_catalog.allocation`(direct/pop_weighted/idw/broadcast)으로 데이터 관리. 각 값에 `source_resolution`·`as_of_year` 동반 저장.
- **처리 위치 = `services/pipeline` Python 오프라인 사전계산**(필요 시 geopandas). PostGIS 런타임 의존을 도입하지 않음 — DB는 결과(long-format `neighborhood_metrics` + `region_boundaries` jsonb)만 저장하고 점수는 MV로 사전계산.

## Consequences

- KOSIS↔SGIS 무매핑 조인으로 큰 통합 리스크 제거.
- PostGIS 미도입 → 기존 Neon 스택(ADR-010) 유지, 운영 단순. 공간 연산은 배치에서 1회.
- 좌표 변환 단계가 ETL에 추가되지만 읍면동 경계는 갱신이 드물어 비용 작음.

## Alternatives Considered

- PostGIS 활성화 후 런타임 공간조인: 운영 복잡·런타임 비용 → 기각(배치 사전계산으로 충분).
- 법정동 코드 기준 통일: SGIS·KOSIS가 통계청 코드라 불필요한 변환만 늘어 기각.

## Related

- [ADR-010](ADR-010-database-stack-migration.md), [ADR-015](ADR-015-livability-score-formula.md)
