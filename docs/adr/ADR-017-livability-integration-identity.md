# ADR-017 — '동네' 거주적합도 통합과 정체성 경계

- **Status**: Accepted
- **Date**: 2026-06-14

## Context

공무원맵은 "공개기록 기반 식당 신호 — 감시·고발·맛평가가 아님"으로 정체성을 명확히 한다([README.md](../../README.md), [PRD.md](../PRD.md), [RISK_MITIGATION.md](../RISK_MITIGATION.md)). 여기에 거주적합도 추천을 더하면 ① 브랜드가 흐려지고 ② "공무원 많이 가는 동네 = 부패?" 식 오독 위험이 있다. 통합 구조를 결정한다.

## Decision

- **공무원맵 한 지붕 + 별도 탭 「살기 좋은 동네」**(사용자 노출명; 내부 코드·라우트는 `동네`/`/neighborhood`로 잔존, 정체성 경계 불변). 서브브랜드·별도 도메인 분리 안 함. (네이밍 근거: [ADR-018](ADR-018-livability-reason-summary-and-why-as-map.md)·[CONTEXT.md](../../CONTEXT.md))
- **거주 점수와 공무원 식당 데이터 완전 분리**: 점수 혼합 절대 금지, API 독립(`/api/v1/neighborhoods/*` vs `/api/v1/places`). 결합은 프론트에서만.
- **크로스링크는 단방향·보조**: 읍면동 상세의 "이 동네 공무원픽 맛집" 카드 → 기존 지도(`/?region=&placeId=`)로 이동. 출처(업무추진비 공개기록) 명시.
- **`/neighborhood` 면책 배너**: "공개 통계 기반 거주 참고 지표이며 공무원 개인을 평가하지 않습니다." SGIS·KOSIS 출처와 업무추진비 출처를 구분 표기.
- **정체성 위계**: 핵심 = 업무추진비 투명성(불변), 인접 = 거주 참고 지표. README·about에 한 줄 명시.
- **`RISK_MITIGATION.md` No-Go에 "동네 절대등급 금지" 추가**([ADR-015](ADR-015-livability-score-formula.md)와 정합).

## Consequences

- 한 지붕 단일 브랜드 → 운영·도메인 단순. 탭 추가만으로 IA 확장.
- 데이터·점수 분리로 "감시 서비스" 오독 방지. 크로스링크로 유니크 시너지(거주+로컬 공무원픽) 유지.
- 거주추천이 식당 신호와 섞이지 않아 법적/평판 리스크 격리.

## Alternatives Considered

- 같은 지도 모드전환(업무추진비 ↔ 거주): 시너지 최대지만 정체성 혼동 → 기각.
- 서브브랜드 분리(별도 도메인): 정체성 명확하나 운영 분산·시너지 약화 → 기각.
- 완전 분리(크로스링크 없음): 차별점 상실 → 기각.

## Related

- [ADR-015](ADR-015-livability-score-formula.md), [ADR-016](ADR-016-livability-spatial-data.md), [RISK_MITIGATION.md](../RISK_MITIGATION.md)
