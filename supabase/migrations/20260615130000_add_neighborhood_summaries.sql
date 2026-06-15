-- 동네 요약 캐시 — "이 동네, 왜 살기 좋을까?" 한 줄 요약 (ADR-018)
-- 런타임은 이 테이블을 읽기만 한다. 채우는 주체는 월배치:
--   ① 룰 claim 엔진(결정론적)이 강점/약점 claim + deterministic 요약을 생성 → source='rule'
--   ② LLM 윤색이 claim을 자연스러운 문장으로 다듬고 출력 게이트를 통과하면 → source='llm'
--   ③ 게이트 실패/키 없음 → ① 결과를 그대로 폴백으로 둔다.
-- claims에 근거(category/kind/rank/total/percentile)를 함께 저장해 표시·검증·재현에 쓴다.

CREATE TABLE IF NOT EXISTS public.neighborhood_summaries (
  adm_cd          text     NOT NULL,
  household_size  smallint NOT NULL,
  profile_version smallint NOT NULL DEFAULT 1,
  summary         text     NOT NULL,
  claims          jsonb    NOT NULL DEFAULT '[]'::jsonb,
  source          text     NOT NULL DEFAULT 'rule',   -- 'rule' | 'llm'
  model           text,                               -- LLM 윤색 시 사용 모델
  generated_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (adm_cd, household_size, profile_version),
  CONSTRAINT neighborhood_summaries_source_chk CHECK (source IN ('rule', 'llm'))
);

COMMENT ON TABLE public.neighborhood_summaries IS
  '동네 한 줄 요약 캐시(월배치 생성). source=rule(결정론적) | llm(윤색 게이트 통과). 런타임은 읽기 전용.';
