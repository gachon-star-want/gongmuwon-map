"""동네 한 줄 요약 — 룰 claim 엔진 + 출력 게이트 + LLM 윤색 (ADR-018)

3중 방어:
  ① build_claims  : field_score(시군구 내 percentile)에서 강점/약점 claim을 결정론적으로 도출
  ② render_rule_summary : claim만으로 deterministic 요약문 생성(LLM 없이도 동작 = 폴백)
  ③ polish_summary : LLM이 ②를 자연스럽게 윤색하되, passes_gate를 통과해야만 채택.
                     게이트 실패/키 없음/예외 → ②로 폴백.

요약은 facts-locked다. LLM에는 숫자를 주지 않고 "어떤 분야가 강점/약점"인지만 주며,
출력 게이트가 (길이·금지어·강점 분야 누락)을 검사해 날조·과장·절대등급을 차단한다.
프론트(NeighborhoodPage)의 CATEGORY_LABEL/STRENGTH와 표기를 일치시킨다.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from public_officer_pipeline.llm.schema import TaskType

# 프론트(apps/web/.../NeighborhoodPage.tsx)와 동일 표기
CATEGORY_LABEL: dict[str, str] = {
    "convenience": "생활편의",
    "safety": "안전",
    "housing": "주택",
    "education": "교육·보육",
    "vitality": "인구·활력",
    "environment": "자연·환경",
    "welfare": "복지·문화",
    "demographics": "인구구성",
}

# 강점일 때 붙이는 객관적 근거 문장(프론트 CATEGORY_STRENGTH와 일치)
CATEGORY_STRENGTH: dict[str, str] = {
    "convenience": "생활편의·일자리가 가깝고 풍부해요",
    "education": "보육·교육 인프라 접근이 좋아요",
    "vitality": "젊고 활기 있는 인구 구성이에요",
    "welfare": "의료·문화 시설이 가까워요",
    "safety": "치안 여건이 상대적으로 좋아요",
    "housing": "주거 환경이 상대적으로 양호해요",
    "environment": "자연·환경 여건이 좋아요",
}

HOUSEHOLD_LABEL: dict[int, str] = {
    0: "거주자",  # 가구원수 무관 공통 요약
    1: "1인 가구",
    2: "신혼·2인 가구",
    3: "자녀·3인 가구",
    4: "자녀·4인 이상 가구",
}

# 절대등급·과장·낙인 차단(ADR-015: 동네에 절대등급 금지)
_BANNED_TOKENS = (
    "최고", "최악", "1위", "꼴찌", "베스트", "워스트", "최상", "최하",
    "나쁜", "안 좋은", "살기 나쁜", "best", "worst", "top1", "no.1",
)


@dataclass
class Claim:
    category: str
    kind: str  # 'strength' | 'weakness'
    rank: int
    total: int
    percentile: float

    @property
    def top_pct(self) -> int:
        if self.total <= 0:
            return 100
        return round(self.rank / self.total * 100)

    @property
    def label(self) -> str:
        return CATEGORY_LABEL.get(self.category, self.category)

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "kind": self.kind,
            "rank": self.rank,
            "total": self.total,
            "percentile": round(self.percentile, 2),
            "top_pct": self.top_pct,
        }


@dataclass
class SummaryResult:
    summary: str
    claims: list[Claim] = field(default_factory=list)
    source: str = "rule"  # 'rule' | 'llm'
    model: str | None = None

    def claims_json(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self.claims]


def build_claims(fields: list[dict[str, Any]]) -> list[Claim]:
    """field 단위 percentile rank로 강점(상위 1/3)·약점(하위 1/3) claim 도출.

    fields 항목: {category, rank, total, percentile}. 프론트 칩 산식과 동일:
      강점 = rank <= ceil(total/3), 약점 = rank >= ceil(total*2/3).
    """
    claims: list[Claim] = []
    for f in fields:
        total = int(f.get("total") or 0)
        rank = int(f.get("rank") or 0)
        if total <= 0 or rank <= 0:
            continue
        strong_cut = math.ceil(total / 3)
        weak_cut = math.ceil(total * 2 / 3)
        if rank <= strong_cut:
            kind = "strength"
        elif rank >= weak_cut:
            kind = "weakness"
        else:
            continue
        claims.append(
            Claim(
                category=str(f["category"]),
                kind=kind,
                rank=rank,
                total=total,
                percentile=float(f.get("percentile") or 0.0),
            )
        )
    return claims


def _strengths(claims: list[Claim]) -> list[Claim]:
    return sorted([c for c in claims if c.kind == "strength"], key=lambda c: c.rank)


def render_rule_summary(claims: list[Claim], sigungu_name: str) -> str:
    """LLM 없이도 동작하는 결정론적 요약(폴백). 프론트 summary 산식과 동일."""
    strengths = _strengths(claims)
    names = [c.label for c in strengths[:2]]
    if names:
        return f"같은 {sigungu_name} 안에서 {'·'.join(names)}이(가) 돋보이는 동네예요."
    return f"같은 {sigungu_name} 안에서 고르게 평균적인 동네예요."


def build_polish_prompt(
    claims: list[Claim],
    region_name: str,
    sigungu_name: str,
    household: int,
) -> str:
    """facts-locked 윤색 프롬프트. 숫자는 주지 않고 강점/약점 분야만 제공."""
    strengths = [c.label for c in _strengths(claims)]
    weaknesses = [c.label for c in claims if c.kind == "weakness"]
    hh = HOUSEHOLD_LABEL.get(household, f"{household}인 가구")
    strength_txt = ", ".join(strengths) if strengths else "(뚜렷한 강점 없음)"
    weakness_txt = ", ".join(weaknesses) if weaknesses else "(뚜렷한 약점 없음)"
    return (
        "너는 공공 통계 기반 거주 안내 카피라이터다. "
        f"'{sigungu_name}' 안에서 '{region_name}'을(를) {hh} 관점으로 한 문장 소개한다.\n\n"
        f"- 강점 분야: {strength_txt}\n"
        f"- 약점 분야: {weakness_txt}\n\n"
        "규칙(반드시 지킬 것):\n"
        "1) 위에 적힌 강점 분야만 근거로 쓴다. 목록에 없는 분야의 우수성을 지어내지 않는다.\n"
        "2) 같은 시군구 안에서의 '상대 비교'임을 전제로 한다. 절대등급·순위·과장 표현 금지"
        "('최고/1위/베스트/나쁜' 등 사용 금지).\n"
        "3) 담백하고 따뜻한 한 문장(공백 포함 60자 이내), '~예요/~동네예요'체.\n"
        "4) 숫자·퍼센트를 쓰지 않는다.\n\n"
        '결과는 {"summary": "..."} JSON으로만 답한다.'
    )


def passes_gate(text: str, claims: list[Claim]) -> bool:
    """LLM 출력 게이트 — 통과해야만 윤색을 채택한다."""
    if not text:
        return False
    if len(text) > 80:
        return False
    lowered = text.lower()
    for token in _BANNED_TOKENS:
        if token.lower() in lowered:
            return False
    # 강점이 있으면, 강점 분야 라벨의 토큰 중 하나라도 본문에 있어야 한다(날조 방지)
    strengths = _strengths(claims)
    if strengths:
        tokens: list[str] = []
        for c in strengths:
            tokens.extend(t for t in c.label.split("·") if t)
        if not any(tok in text for tok in tokens):
            return False
    return True


async def polish_summary(
    client: Any,
    claims: list[Claim],
    region_name: str,
    sigungu_name: str,
    household: int,
) -> tuple[str, str] | None:
    """LLM 윤색 1회. 게이트 통과 시 (text, model), 아니면 None(→ 폴백)."""
    prompt = build_polish_prompt(claims, region_name, sigungu_name, household)
    schema = {
        "type": "object",
        "required": ["summary"],
        "properties": {"summary": {"type": "string"}},
    }
    try:
        result = await client.extract(
            task=TaskType.NEIGHBORHOOD_SUMMARY_POLISH,
            prompt=prompt,
            schema=schema,
        )
    except Exception:
        return None
    text = str(result.payload.get("summary") or "").strip()
    if not passes_gate(text, claims):
        return None
    return text, result.model


async def generate_summary(
    *,
    client: Any | None,
    fields: list[dict[str, Any]],
    region_name: str,
    sigungu_name: str,
    household: int,
) -> SummaryResult:
    """동네 요약 1건 생성. client=None이거나 게이트 실패 시 결정론적 폴백."""
    claims = build_claims(fields)
    rule_text = render_rule_summary(claims, sigungu_name)
    if client is not None and any(c.kind == "strength" for c in claims):
        polished = await polish_summary(client, claims, region_name, sigungu_name, household)
        if polished is not None:
            text, model = polished
            return SummaryResult(summary=text, claims=claims, source="llm", model=model)
    return SummaryResult(summary=rule_text, claims=claims, source="rule", model=None)


__all__ = [
    "Claim",
    "SummaryResult",
    "build_claims",
    "render_rule_summary",
    "build_polish_prompt",
    "passes_gate",
    "polish_summary",
    "generate_summary",
    "CATEGORY_LABEL",
    "CATEGORY_STRENGTH",
    "HOUSEHOLD_LABEL",
]
