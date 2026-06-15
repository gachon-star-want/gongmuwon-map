# ADR-018 — '왜 좋은지' 요약 생성 + 강점 렌즈 지도(Why-as-Map)

- **Status**: Accepted
- **Date**: 2026-06-15

## Context

'살기 좋은 동네'에서 동을 고르면 **"왜 살기 좋은지"를 객관 데이터로** 보여줘야 한다. raw 숫자 나열은 금지(사용자 불만의 핵심). ① 자연어 요약을 어떻게 생성할지 ② 지도로 '왜'를 어떻게 시각화할지를 결정한다. [ADR-015](ADR-015-livability-score-formula.md)(절대등급 금지·시군구 내 percentile)·[ADR-016](ADR-016-livability-spatial-data.md)(오프라인 사전계산) 제약 하에서.

**결정적 코드 사실**: `neighborhood_scores_v1` MV는 CTE에서 지표별 percentile(`mscore`)·분야별 percentile(`field_score`)을 계산하지만 최종 SELECT에서 **종합점수 하나로 뭉개 버린다**. 강점/약점·분야 렌즈는 이 버려지는 중간값 없이는 불가능하다.

## Decision

**요약 생성 = Facts-locked, LLM-polished, precomputed (3중 방어):**
1. **룰 엔진**이 검증된 `claim` 카드(분야·시군구 내 percentile·근거지표·신뢰도)만 결정론적으로 산출. 강점 = 상위 1/3, 약점 = 하위 1/3, ADR-015 컷(`pct<0.40` 미부여).
2. **월배치**(`.github/workflows/livability-monthly.yml`)에서 claim만 LLM에 넘겨 한 줄 카피로 윤색 → **DB 캐시**. 런타임은 캐시 읽기뿐(실시간 LLM 금지).
3. **출력 게이트**: 길이·금칙어(절대등급/낙인/'나쁜')·시설명 화이트리스트 검증. 실패 시 **순수 룰 템플릿 문장으로 deterministic 폴백**(LLM 없이도 항상 답이 나옴).

**강점 렌즈 지도(Why-as-Map):** choropleth에 분야 렌즈 칩(데이터가 실제 있는 category만 동적 렌더 — MVP는 종합·생활편의·교육보육·인구활력·복지문화 5개). 색 = 시군구 내 percentile 단색 5분위(단일 hue, **빨강=나쁨 금지**). 결측 = 빗금(점수 0과 시각 분리). 지도 위 텍스트 핀(reason-pin)은 **비채택**(경계 미제공 동 오독 = 사실상 절대등급).

**선행 데이터 작업(필수):** 버려지던 `field_score`(분야 percentile)를 보조 산출물(MV/테이블)로 **보존**하고 `boundaries`/`detail` API에 노출. 런타임 PERCENT_RANK 재계산 금지(ADR-016).

**POI:** 가중치 큰 분야에만 외과적 수집(학교알리미·LOCALDATA), **점수에 가산하지 않고** 근거 표시 전용.

## Consequences

- 환각·비용·일관성: 입력잠금 + 월배치 + 폴백으로 3중 차단. AI 비용은 동당 월 1회 소액.
- 분야 percentile 보존이 강점/약점 칩·렌즈의 전제 → 백엔드 선행 작업 발생("프론트만 고치면 됨"은 거짓).
- POI 근거 표시 전용 → 결측 0점 금지(ADR-015) 정합.

## Alternatives Considered

- 순수 LLM 실시간 생성: 수만 조합 비용·지연·환각·비결정성 → 기각.
- 순수 룰 템플릿: 안전하나 카피 매력 낮음 → **폴백**으로 채택(코어는 하이브리드).
- 지도 reason-pin: 경계 미제공 동 오독 → 기각, 강점/약점은 패널 칩으로.

## Related

- [ADR-015](ADR-015-livability-score-formula.md), [ADR-016](ADR-016-livability-spatial-data.md), [ADR-017](ADR-017-livability-integration-identity.md), [CONTEXT.md](../../CONTEXT.md)
