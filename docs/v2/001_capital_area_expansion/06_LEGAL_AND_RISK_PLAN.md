# 06 — Legal & Risk Plan

- **Status**: Implemented (plan2b ownership)
- **Date**: 2026-05-25

## 1. Purpose

Re-confirm that v2 stays inside the v1 legal/privacy envelope, enumerate the v2-specific risks (new jurisdictions, new publication formats, expanded elected-official set), and define complaint/takedown handling for the new regions.

> **[docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) is the final authority.** Nothing in this document overrides it. Where v2 needs a policy detail the v1 doc does not yet spell out (e.g. governor/county-head roles), this document flags it as a **doc-update prerequisite**, not a new rule invented here.

## 2. Re-confirmation of v1 legal basis (applies unchanged to Gyeonggi/Incheon)

**[FACT]** v1's four-layer legal basis ([docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) §"법적 근거 4겹") is national law, not Seoul-specific, and applies identically to Gyeonggi-do and Incheon:

1. 「공공기관의 정보공개에 관한 법률」 제9조 1항 6호 가목 — 직무 수행 공무원의 성명·직위는 공개 대상.
2. 「지방자치단체 업무추진비 집행에 관한 규칙」 + 행안부 「업무추진비 집행내역 공개기준」(별표 6) — mandatory fields (집행일시/장소/목적/대상/금액/결재방법) are the same nationwide.
3. 공공누리 제1유형 — public-domain commercial-use + derivative license (confirm per-source during verification, [02_SOURCE_REGISTRY_PLAN.md](02_SOURCE_REGISTRY_PLAN.md) §6).
4. 사실 적시 명예훼손 위법성 조각 (형법 310조) — public-interest / public-figure doctrine applies the same.

→ The same legality argument that covers Seoul covers the capital-area expansion. No new legal theory is required.

## 3. Forbidden features — reaffirmed (v1 merge-block policy)

**[FACT]** Carried over from [docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) §"위반 시 머지 금지" and [docs/RISK_MITIGATION.md](../../RISK_MITIGATION.md) §"No-Go", with the later [ADR-012](../../adr/ADR-012-community-auth-and-lightweight-reactions.md) narrowing applied. v2 data expansion must **not** add any of:

- ❌ User comments, ratings, or reviews on restaurant/place pages (defamation risk).
- ❌ New community or reaction scope beyond ADR-012 as part of this data rollout.
- ❌ Storing personal real names in plaintext and masking at display time (masking must happen at load time).
- ❌ Omitting source attribution.
- ❌ Weakening the disclaimer / terms.
- ❌ A structure that misses the 72h notice-and-takedown SLA.
- ❌ Labeling officials as corrupt / inferring personal habits / "고급·저급" pricing judgments / "진짜 맛집" marketing.

These are non-negotiable for v2 exactly as for v1.

## 4. Masking by rank — extended for new jurisdictions

**[FACT, v1]** The masking tiers ([docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) §"우리 표기 정책"):

| Tier | Treatment |
|---|---|
| Elected senior officials | Real name + rank OK |
| Appointed senior officials | Rank + department, name masked |
| Rank-5-and-below | Department + "○○과 외 N명", name & rank masked |
| Private attendees | Masked, "민간 외 N명" |
| Restaurant / address / date / amount / party size / purpose / payment / category | Verbatim |

**v2 extension — the elected-official set must be enumerated for the new regions.** Seoul's list is 시장 / 구청장 / 시의원 / 구의원. The capital-area equivalents are:

| Region | Elected (name+rank OK) | Appointed (mask name) |
|---|---|---|
| Gyeonggi province | 도지사, 도의원 | 부지사, 실·국장 등 |
| Gyeonggi 시·군 | 시장·군수, 시의원·군의원 | 부시장·부군수, 국·과장 등 |
| Incheon metro | 시장(인천시장), 시의원(광역) | 부시장, 실·국장 등 |
| Incheon 군·구 | 구청장·군수, 구의원·군의원 | 부구청장·부군수, 국·과장 등 |

**[IMPLEMENTED BY PLAN2B]** The following must stay consistent with this policy:

1. [docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) (the authority)
2. The LLM masking system prompt ([docs/PIPELINE.md](../../PIPELINE.md) §"마스킹 룰").
3. The masking SQL allowlist ([04_DATA_QUALITY_PLAN.md](04_DATA_QUALITY_PLAN.md) §3) — query (1)'s `IN (...)` set.

## 5. Attribution — preserved and extended **[FACT]**

The footer / `/legal` / `llms.txt` / OpenAPI must keep **"공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외"**. For v2:

- Keep the base string.
- Update "외 N개 기관" to reflect 138 total agencies once fully rolled out.
- Add each verified Gyeonggi/Incheon source (agency, URL, license, last-updated) to the `/legal` per-source list as it is verified.
- Per-source license must be individually confirmed (§2.3) — do not assume 공공누리 제1유형 universally without checking each portal.

## 6. Complaint / takedown / correction handling (new regions)

**[FACT]** Reuse v1's 4-layer defense and per-scenario playbook ([docs/RISK_MITIGATION.md](../../RISK_MITIGATION.md)) unchanged — they are not Seoul-specific:

- **Notice-and-takedown**: immediate `hidden_at` on request, 72h operator review, 정통망법 44조의2 compliant.
- **Per-scenario**: official's "remove my info", local-government protest, restaurant-owner request, court injunction (highest priority, operator address for service), 방심위 / 개인정보위 / press.
- **Abstraction toggle** (`?abstraction=high`) still applies.

v2-specific considerations:

- **More local governments = more potential complainants.** 86 new agencies means more 시·군·구 smaller offices whose staff may object. The same masking tiers protect them; the rank-5-and-below and appointed-official masking is what limits exposure.
- **Operator contact unchanged** ([AGENTS.md](../../../AGENTS.md) / [docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md)): 이원영/WonYoungLee, wylee0806@naver.com, 010-7133-0806, 경기도 성남시 분당구 수내로 39. This stays the single point for service/takedown across all regions. (Note: the operator's own address is in Gyeonggi — no special handling needed, just awareness.)
- **Injunction backup**: targeted-delete-by-`agency_id` ([05_DB_ROLLOUT_PLAN.md](05_DB_ROLLOUT_PLAN.md) §6) makes per-agency or per-place removal clean if a court orders it.

## 7. Risk: per-jurisdiction publication-format differences

This is the largest **operational** (not legal) v2 risk: Gyeonggi/Incheon agencies publish 업무추진비 in inconsistent ways.

| Risk | Likelihood | Mitigation |
|---|---|---|
| Heavy HWP/HWPX reliance | **[ASSUMPTION] high** for some agencies | Validate extractor path on Incheon batch first; LLM-vision fallback; quarantine sub-threshold agencies ([04_DATA_QUALITY_PLAN.md](04_DATA_QUALITY_PLAN.md) §2). |
| Scanned (image) PDFs | medium | Route to Claude vision (ADR-009); higher sampling; confirm masking on vision output. |
| Shorter online history | medium | Accept shorter backfill; record in registry `notes`; never fabricate missing months. |
| No online disclosure (paper / 정보공개청구 only) | low–medium | Mark agency as such in `notes`; exclude from crawl rather than guess. |
| Per-일반구 publication (large Gyeonggi 시) | medium | Surfaces in dry-run; decide agency split via registry before loading ([01_SCOPE.md](01_SCOPE.md) §3.1). |
| Inconsistent column layout vs 별표 6 | medium | LLM general extraction tolerates layout drift; schema validator + confidence gate catch failures. |
| Robots.txt / access constraints | low | Recorded during verification ([02_SOURCE_REGISTRY_PLAN.md](02_SOURCE_REGISTRY_PLAN.md) §6); respect site rules. |

A format the pipeline genuinely cannot handle becomes a **tracked blocker**, not a silent data gap — consistent with the "no fabrication" rule.

## 8. Risk: cross-region name collisions (legal-adjacent)

중구/동구/서구 exist in multiple cities. Mis-attributing a visit to the wrong region's agency could misrepresent an official. Mitigation: agency natural key includes region (`parent_region` + `sub_region`), and entity resolution keys on coordinates/placeId, not name ([02_SOURCE_REGISTRY_PLAN.md](02_SOURCE_REGISTRY_PLAN.md) §4.3, [04_DATA_QUALITY_PLAN.md](04_DATA_QUALITY_PLAN.md) §5). Verified explicitly in the dry-run.

## 9. What this stage does NOT do

- Does not add new legal policy beyond the 수도권 선출직/임명직 확장 already documented above.
- Does not process any real complaint.
- It only re-confirms the policy envelope and enumerates v2 risks and prerequisites.
