# ADR-009 — 멀티 LLM 프로바이더 라우팅 (Anthropic + OpenAI + Gemini)

- **Status**: Accepted
- **Date**: 2026-05-23
- **Supersedes**: ADR-002의 "단일 Anthropic 의존" 부분(나머지 결정은 유지)

## Context

[ADR-002](ADR-002-llm-extraction.md)에서 Anthropic Claude 단일 의존을 채택했으나, 다음 리스크·기회가 식별됨:

| 이슈 | 단일 프로바이더 한계 |
|---|---|
| **장애 대응** | Anthropic API 장애 시 파이프라인 전체 정지 |
| **비용 최적화** | 같은 작업도 프로바이더별 토큰 단가·할인이 다름 |
| **모델별 강점** | 한국어 표 추출은 Gemini Flash가 우수하고, 수치 정형화는 GPT-4o-mini가 우수한 사례 등 |
| **레이트 리밋** | 단일 프로바이더 한도 도달 시 다음 사이클까지 정체 |

## Decision

**3개 프로바이더를 동시에 환경변수로 두고, 작업 유형·confidence·비용에 따라 라우팅한다.**

### 환경변수 (모두 GitHub Secret + Vercel/Supabase env)
```
ANTHROPIC_API_KEY
OPENAI_API_KEY
GEMINI_API_KEY
LLM_PRIMARY=anthropic     # 기본 진입 프로바이더 (변경 가능)
LLM_FALLBACK_ORDER=openai,gemini,anthropic-sonnet
LLM_BUDGET_DAILY_USD=10   # 일일 예산 상한 (초과 시 강등)
```

### 모델 라우팅 매트릭스

| 작업 유형 | 1차 | 2차 (confidence < 0.8) | 3차 (1·2차 실패) |
|---|---|---|---|
| **대량 표 정규화** (HTML·XLSX) | Gemini 2.5 Flash | Claude Haiku 4.5 | GPT-4o-mini |
| **PDF 표 추출** (text-based) | Claude Haiku 4.5 | Gemini 2.5 Flash | Claude Sonnet 4.6 |
| **PDF 비전(스캔 이미지)** | Claude Sonnet 4.6 vision | Gemini 2.5 Pro vision | GPT-4o vision |
| **식당명 정규화 (까다로움)** | Claude Sonnet 4.6 | GPT-4o | Gemini 2.5 Pro |
| **사이트 어댑터 구조 추론** | Claude Sonnet 4.6 | GPT-4o | — |
| **마스킹 검증 (보안 critical)** | Claude Sonnet 4.6 | Claude Sonnet 4.6 (재시도) | 사람 큐 |

### 비용 가드레일
- 일일 예산 초과 → 자동 강등(가장 싼 모델로 1주 운영) + 알림.
- 호출 단위 토큰 사용량 기록 → `llm_usage` 테이블에 적재.
- 주간 리포트: 프로바이더별 호출 수·비용·에러율·평균 confidence.

### 폴백 트리거
1. **5xx / 429** → 즉시 다음 프로바이더로 재시도(같은 모델 동급 → 다른 프로바이더)
2. **타임아웃 30초** → 다음 프로바이더
3. **schema validation 실패** → 같은 프로바이더 1회 재시도 후 다음 프로바이더
4. **confidence < 0.8 평균** → escalate (다음 행)

### 통일 인터페이스
```python
# services/pipeline/normalizer/llm_client.py
class LLMClient:
    async def extract(
        self,
        task: TaskType,            # TABLE_NORMALIZE | PDF_EXTRACT | VISION | NAME_NORMALIZE | ...
        prompt: str,
        schema: JSONSchema,
        timeout: int = 30,
    ) -> ExtractResult: ...
```

- 내부에서 `task` + `LLM_PRIMARY` + 폴백 순서로 자동 라우팅
- 모든 응답은 동일 `ExtractResult` 형식 (provider·model·tokens·confidence 메타 포함)
- 호출자는 어느 프로바이더가 응답했는지 알 필요 없음

## Consequences

### 긍정
- 어느 한 프로바이더 장애에도 파이프라인 무중단.
- 모델별 강점 활용 → 정확도 + 비용 동시 최적화 가능.
- 신규 프로바이더(예: xAI Grok, Mistral) 추가 쉬움.
- A/B 비교용 데이터 자동 수집(`llm_usage`).

### 부정
- 통일 인터페이스 추상화 비용 (≈1일 분량 추가 구현).
- 프로바이더별 schema/tool 호환성 차이 → 시스템 프롬프트 분기 필요.
- 응답 형식 정규화 부담 (특히 Gemini의 JSON 모드와 OpenAI structured output, Anthropic tool_use가 미세 다름).

### 리스크
- 멀티 프로바이더로 인한 정책 일관성 흔들림 → 마스킹 룰은 **시스템 프롬프트로 박되, 출력 후 schema validator로 한 번 더 검증** (이미 ADR-002 정책).
- 비용 예측 어려움 → 일일 예산 가드레일 필수.

## Alternatives Considered

- **단일 프로바이더 유지** (ADR-002): 단순하지만 장애 리스크.
- **Vercel AI Gateway / OpenRouter** 같은 단일 게이트웨이 사용: 통일 인터페이스 + rate limit 관리. **v1.1에서 검토** (도입 비용 < 운영 단순화 이득이면 채택).
- **로컬 모델 (Ollama·llama.cpp)**: 비용 0이지만 한국어 표 추출 정확도 부족, GitHub Actions 환경에서 실행 부담.

## Migration Path

ADR-002의 "1차 Haiku, 폴백 Sonnet" 로직은 **본 ADR의 라우팅 매트릭스에 흡수**. PIPELINE.md / TECH_STACK.md / RUNBOOK.md 동시 업데이트.

## Related

- [ADR-002](ADR-002-llm-extraction.md), [PIPELINE.md](../PIPELINE.md), [TECH_STACK.md](../TECH_STACK.md)
