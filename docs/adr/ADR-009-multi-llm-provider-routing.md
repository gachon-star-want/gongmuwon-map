# ADR-009 — 멀티 LLM 프로바이더 라우팅 (Anthropic + OpenAI + Gemini)

- **Status**: Accepted
- **Date**: 2026-05-23 (initial) · **2026-05-24 (model refresh + thinking/reasoning budgets)**
- **Supersedes**: ADR-002의 "단일 Anthropic 의존" 부분(나머지 결정은 유지)

## Context

[ADR-002](ADR-002-llm-extraction.md)에서 Anthropic Claude 단일 의존을 채택했으나, 다음 리스크·기회가 식별됨:

| 이슈 | 단일 프로바이더 한계 |
|---|---|
| **장애 대응** | Anthropic API 장애 시 파이프라인 전체 정지 |
| **비용 최적화** | 같은 작업도 프로바이더별 토큰 단가·할인이 다름 |
| **모델별 강점** | 한국어 표 추출은 Gemini Flash가 우수, 수치 정형화는 GPT가 우수한 사례 등 |
| **레이트 리밋** | 단일 프로바이더 한도 도달 시 다음 사이클까지 정체 |

또한 2026년 들어 세 프로바이더 모두 **명시적 thinking/reasoning budget 옵션**을 노출(Anthropic extended thinking, OpenAI `reasoning.effort`, Gemini `thinking_level`). 같은 모델이라도 reasoning depth에 따라 정확도·비용이 크게 변동하므로 작업 유형별로 budget을 명시적으로 박아야 함.

## Decision

**3개 프로바이더를 동시에 환경변수로 두고, 작업 유형 + confidence + 비용 + reasoning depth에 따라 라우팅한다.**

### 환경변수 (모두 GitHub Secret + Vercel env)
```
ANTHROPIC_API_KEY
OPENAI_API_KEY
GEMINI_API_KEY
LLM_PRIMARY=anthropic            # 기본 진입 프로바이더 (변경 가능)
LLM_FALLBACK_ORDER=openai,gemini,anthropic-opus
LLM_BUDGET_DAILY_USD=10          # 일일 예산 상한 (초과 시 강등)
```

### 모델 라우팅 매트릭스 (2026-05-24 기준)

| 작업 유형 | 1차 (모델 · thinking/reasoning) | 2차 (confidence<0.8) | 3차 (1·2차 실패) |
|---|---|---|---|
| **대량 표 정규화** (HTML·XLSX) | Gemini 3.5 Flash · `thinking_level=minimal` | Claude Haiku 4.5 · extended thinking off | GPT-5.5 · `reasoning.effort=low` |
| **PDF 표 추출** (텍스트 기반) | Claude Haiku 4.5 · extended thinking off | Gemini 3.5 Flash · `thinking_level=low` | Claude Sonnet 4.6 · extended thinking 4K |
| **PDF 비전** (스캔 이미지) | **Claude Opus 4.7 vision** · extended thinking 8K | Gemini 3.5 Flash vision · `thinking_level=medium` | GPT-5.5 · `reasoning.effort=medium` |
| **식당명 정규화** (까다로움) | Claude Sonnet 4.6 · extended thinking 4K | GPT-5.5 · `reasoning.effort=medium` | Claude Opus 4.7 · extended thinking 4K |
| **사이트 어댑터 구조 추론** (일회성) | Claude Opus 4.7 · extended thinking 32K | GPT-5.5 · `reasoning.effort=high` | — |
| **마스킹 검증** (보안 critical) | Claude Sonnet 4.6 · extended thinking 16K | Claude Sonnet 4.6 재시도 · extended thinking 16K | **사람 큐** |

**모델 선정 논리**:
- **워크호스 1차**: Gemini 3.5 Flash (2026-05-19 출시, $1.50/$9 per M tokens, Gemini 3.1 Pro급 성능을 4x 빠르게)
- **PDF 비전 1차**: Claude Opus 4.7 (2026-04 출시, vision 해상도 3x 점프 — 스캔된 한국어 표 인식 결정타)
- **마스킹 검증**: 항상 Claude Sonnet 4.6 + high thinking — 보안 critical, 사고 비용 >> 토큰 비용
- **대량 처리**: thinking off 또는 minimal — 비용 폭주 방지
- **일회성 고가치**: high reasoning + 최상위 모델 (사이트 어댑터 추론은 기관당 한 번만)

### Thinking / Reasoning 파라미터 매핑

각 프로바이더는 reasoning depth 파라미터의 형식이 다름. 호출자는 작업 유형만 명시하고 라우터가 프로바이더별로 변환:

| 프로바이더 | 파라미터 | 값 도메인 | 본 ADR에서 사용하는 값 |
|---|---|---|---|
| **Anthropic** | `extended_thinking.budget_tokens` | 정수 (최소 1024) | off / 1K / 4K / 8K / 16K / 32K — **thinking 토큰도 output 단가로 과금** |
| **OpenAI** | `reasoning.effort` | `none` / `minimal` / `low` / `medium` (default) / `high` / `xhigh` | low / medium / high 사용 |
| **Google** | `thinking_level` (구 `thinking_budget` deprecated) | `minimal` / `low` / `medium` (default) / `high` | **default가 high→medium으로 강등됨** 주의 |

### 비용 가드레일
- 일일 예산 초과 → 자동 강등(가장 싼 모델로 1주 운영) + 알림.
- **thinking 토큰이 output 단가에 합산**되므로 high reasoning을 무분별하게 쓰면 예산 폭주 → 작업별 thinking level을 코드에서 하드코딩(configurable but with sane defaults).
- 호출 단위 토큰 사용량 기록 → `llm_usage` 테이블에 적재(`thinking_tokens` 컬럼 포함).
- 주간 리포트: 프로바이더별·모델별 호출수·비용·에러율·평균 confidence·평균 thinking 토큰.

### 폴백 트리거
1. **5xx / 429** → 즉시 다음 프로바이더로 재시도(같은 모델 동급 → 다른 프로바이더)
2. **타임아웃 30초** → 다음 프로바이더
3. **schema validation 실패** → 같은 프로바이더 1회 재시도 후 다음 프로바이더
4. **confidence < 0.8 평균** → escalate (매트릭스의 다음 행)

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
- **task별 thinking budget은 라우터 내부에서 하드코딩** (호출자는 신경 안 씀)
- 모든 응답은 동일 `ExtractResult` 형식(provider·model·tokens·**thinking_tokens**·confidence 메타 포함)

## Consequences

### 긍정
- 어느 한 프로바이더 장애에도 파이프라인 무중단.
- 모델별 강점 활용 → 정확도 + 비용 동시 최적화 가능.
- 신규 프로바이더(예: xAI Grok, Mistral) 추가 쉬움.
- Thinking budget을 task별로 분리해 비용 컨트롤.
- A/B 비교용 데이터 자동 수집(`llm_usage`).

### 부정
- 통일 인터페이스 추상화 비용 (≈1일 분량 추가 구현).
- 프로바이더별 schema/tool 호환성 차이 → 시스템 프롬프트 분기 필요.
- 응답 형식 정규화 부담 (Gemini JSON 모드, OpenAI structured output, Anthropic tool_use가 미세 다름).
- Thinking 파라미터가 프로바이더별 의미·과금 방식이 달라 매핑 테이블 관리 필요.

### 리스크
- 멀티 프로바이더로 인한 정책 일관성 흔들림 → 마스킹 룰은 **시스템 프롬프트로 박되, 출력 후 schema validator로 한 번 더 검증** (이미 ADR-002 정책).
- 비용 예측 어려움 → 일일 예산 가드레일 + thinking 토큰 추적 필수.

## Alternatives Considered

- **단일 프로바이더 유지** (ADR-002): 단순하지만 장애 리스크.
- **Vercel AI Gateway / OpenRouter** 같은 단일 게이트웨이 사용: 통일 인터페이스 + rate limit 관리. **v1.1에서 검토** (도입 비용 < 운영 단순화 이득이면 채택).
- **로컬 모델 (Ollama·llama.cpp)**: 비용 0이지만 한국어 표 추출 정확도 부족, GitHub Actions 환경에서 실행 부담.

## Migration Path

ADR-002의 "1차 Haiku, 폴백 Sonnet" 로직은 **본 ADR의 라우팅 매트릭스에 흡수**. PIPELINE.md / TECH_STACK.md / RUNBOOK.md / ARCHITECTURE.md 동시 업데이트.

## Re-evaluation TODO

- **Gemini 3.5 Pro 출시 후 (예상 2026-06)** 매트릭스 재검토: 식당명 정규화·사이트 어댑터 추론에서 Pro로 격상 가능성 점검.
- 분기 1회 모델 라인업 갱신 (각 프로바이더 release cadence ≈ 3~6주).
- 신규 변종(GPT-5.5 mini/nano 등) 확정 시 대량 처리 1차 슬롯 비용 절감 검토.

## Related

- [ADR-002](ADR-002-llm-extraction.md), [PIPELINE.md](../PIPELINE.md), [TECH_STACK.md](../TECH_STACK.md), [RUNBOOK.md](../RUNBOOK.md)
