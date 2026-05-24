# ADR-003 — 식당 정체성(Entity Resolution)

- **Status**: Accepted
- **Date**: 2026-05-23

## Context

같은 식당이 원본에 `"창고43시청점"`, `"창고43 시청점"`, `"창고43(시청점)"`처럼 여러 표기로 등장한다. 잘못 결합하면 동일 식당이 여러 row로 쪼개지거나, 다른 식당이 머지된다.

옵션:

1. **자체 정규화 이름 + 도로명 주소만**
2. **카카오 로컬 placeId + (정규화 이름 + geohash) 폴백**
3. **사업자등록번호**

## Decision

**2번: 카카오 placeId 메인 + 자체 자연키 폴백.**

- LLM이 원본에서 `(name, address_hint)` 분해
- 카카오 로컬 검색 API 조회 → placeId·좌표 획득
- 좌표가 입력 주소의 ±300m 안이면 매칭 성공 → `kakao_place_id` 키로 upsert
- 매칭 실패 시 `natural_key = normalize(name) + ':' + geohash7(lat, lng)` 폴백
- 사후에 같은 placeId 발견 시 자동 머지

## Consequences

- 외부 권위 있는 ID(카카오)에 정합 → 향후 카카오맵 연동·검색 정합성↑
- 폐업 식당이 카카오에서도 없으면 자체 키로 보존
- 정규화 룰 단순: 공백·특수문자 제거, 괄호 안 지점명 분리 보존
- 카카오 일 30,000회 한도 → 7일 캐시로 95% 절감

## Risks

- 카카오 매칭 누락 → 점진적 머지 도구 필요(운영자 v1.1)
- 사업자번호 부재로 동일 사업자 다른 지점 확정 어려움 → 지점명 별도 분리로 우회

## Related

- [DATA_MODEL.md](../DATA_MODEL.md#entity-resolution-알고리즘)
