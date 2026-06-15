"""동네 요약 룰 엔진·출력 게이트 테스트 (ADR-018)."""
from __future__ import annotations

from public_officer_pipeline.livability.summary import (
    build_claims,
    passes_gate,
    render_rule_summary,
)


def _fields():
    return [
        {"category": "convenience", "rank": 1, "total": 25, "percentile": 99},
        {"category": "education", "rank": 25, "total": 25, "percentile": 1},
        {"category": "welfare", "rank": 12, "total": 25, "percentile": 50},
    ]


def test_build_claims_strength_weakness_and_middle_excluded():
    claims = build_claims(_fields())
    kinds = {c.category: c.kind for c in claims}
    assert kinds["convenience"] == "strength"
    assert kinds["education"] == "weakness"
    assert "welfare" not in kinds  # 중간(상/하위 1/3 밖)은 claim 없음


def test_build_claims_skips_invalid_total():
    claims = build_claims([{"category": "convenience", "rank": 0, "total": 0, "percentile": 0}])
    assert claims == []


def test_render_rule_summary_uses_sigungu_and_label():
    claims = build_claims([{"category": "convenience", "rank": 1, "total": 9, "percentile": 99}])
    s = render_rule_summary(claims, "충주시")
    assert "충주시" in s and "생활편의" in s


def test_render_rule_summary_no_strength_falls_back():
    s = render_rule_summary([], "충주시")
    assert "고르게 평균적인" in s


def test_gate_accepts_valid_summary():
    claims = build_claims([{"category": "convenience", "rank": 1, "total": 9, "percentile": 99}])
    assert passes_gate("생활편의가 가까운 동네예요", claims)


def test_gate_blocks_banned_tokens():
    claims = build_claims([{"category": "convenience", "rank": 1, "total": 9, "percentile": 99}])
    assert not passes_gate("충주 최고의 동네예요", claims)  # 절대등급/과장 금지어
    assert not passes_gate("살기 나쁜 동네예요", claims)


def test_gate_blocks_missing_strength_label():
    claims = build_claims([{"category": "convenience", "rank": 1, "total": 9, "percentile": 99}])
    # 강점이 생활편의인데 본문에 강점 분야 토큰이 없으면 날조로 간주
    assert not passes_gate("조용하고 살기 좋은 동네예요", claims)


def test_gate_blocks_empty_and_too_long():
    claims = build_claims([{"category": "convenience", "rank": 1, "total": 9, "percentile": 99}])
    assert not passes_gate("", claims)
    assert not passes_gate("생활편의 " * 30, claims)  # 80자 초과
