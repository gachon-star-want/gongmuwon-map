# 02 — Source Registry Plan

- **Status**: Planning (documentation only)
- **Date**: 2026-05-25

> Implementation note (2026-06-01): the code now exposes a generated source registry(출처 등록부) via
> `public-officer-pipeline source-registry --scope capital-area`. Current code-tracked status is
> **138 total / 131 verified_in_code(공식 출처 검증 완료) / 0 pending(검증 대기) /
> 7 legal_hold(법적 검토 보류) / 0 invalid_source_pattern(출처 패턴 오류)**. New 경기·인천 verified entries require official
> homepage/source URL alignment plus `verifiedAt` and `verifiedBy`; unverified agencies stay
> `adapter_required` with no fabricated URL, while legally blocked sources stay `legal_hold` until an ADR/legal decision changes the 제1유형 policy.

## 1. Purpose

Design a per-agency **source registry** for the 86 new capital-area agencies (Gyeonggi 64 + Incheon 22), define the fields each entry needs, and specify how a candidate source is **verified** before it is allowed to drive a crawl.

> **No real source URLs are mass-generated in this document.** Where a URL is unknown, the entry is left as `TODO`. The current Seoul registry already lives in code (`services/pipeline/src/public_officer_pipeline/agencies.py`); v2 mirrors that structure but does not pre-fill unverified URLs.

## 2. Seoul is already fully wired — v2 is purely additive **[FACT]**

**Seoul is effectively done at the source-registry/adapter level.** All 52 Seoul agencies in `agencies.py` carry a concrete `source_pattern.adapter`, and **0 of them remain in an `adapter_required` placeholder state** (verified 2026-05-25 by enumerating `SEOUL_AGENCIES`).

Current Seoul adapter distribution (all 52 assigned):

| Adapter value | Count | Meaning |
|---|---|---|
| `council_attachment_board` | 25 | All 25 district councils — board with attachments. |
| `attachment_board` | 21 | District offices — board with attachment files (pdf/xls/xlsx). |
| `seoul_opengov` | 2 | Seoul City Hall + Seoul Metropolitan Council via 정보소통광장 HTML list. |
| `inline_expense_table` | 2 | Offices that render the expense table inline in HTML (서대문, 은평). |
| `gangnam_xlsx_board` | 1 | Gangnam office — site-specific XLSX board. |
| `estimate_list_html` | 1 | Gwanak office — HTML "estimate" list. |
| **Total** | **52** | **No `*_required` remaining.** |

Beyond the registry, Seoul also has real extraction/crawler code already in the repo (e.g. `crawler/seoul_opengov.py`, `crawler/gangnam.py`, `crawler/estimate.py`, `crawler/inline_table.py`, `crawler/gncouncil.py`, and extractors `extractor/opengov_html.py`, `extractor/spreadsheet.py`, `extractor/pdf_vision.py`).

**Implication for v2:** Seoul needs **no source-registry work**. This document's registry effort is **only the 86 new agencies** (Gyeonggi 64 + Incheon 22). Seoul is the reference template, not a work item.

> Whether Seoul has been *crawled and loaded into production* is a separate operational question (out of scope for this doc-only stage). What is settled here is that Seoul's **sources and adapters are fully defined** and serve as the proven pattern v2 copies.

### 2.1 The `*_required` placeholder convention (for new agencies)

The codebase already has a first-class convention for "agency known, source not yet verified": the `district_board_required` / `district_council_board_required` adapter values with `status: "adapter_required"`. Seoul no longer uses them (count = 0), but **v2 reuses exactly this convention**: every new Gyeonggi/Incheon agency starts as `*_required` until its source passes §6 verification, then gets a concrete adapter — mirroring the path Seoul already completed.

## 3. Registry entry fields

Each new agency gets one registry entry. Required fields:

| Field | Type | Description | Source |
|---|---|---|---|
| `region` | enum | `서울특별시` \| `경기도` \| `인천광역시`. | Known. |
| `jurisdiction_type` | enum | `province` \| `metro_city` \| `autonomous_gu` \| `si` \| `gun` (or other `JurisdictionType` values from ADR-011). Captures the 도/광역시/시/군/구 distinction. | Known from [01_SCOPE.md](01_SCOPE.md). |
| `organization_name` | text | Full official name, e.g. "경기도청", "수원시청", "수원시의회", "인천광역시 강화군청". | Known. |
| `council_or_admin` | enum | `admin` (집행부/청) \| `council` (의회). | Known. |
| `source_url` | text \| `TODO` | The board/list URL where 업무추진비 is published. **`TODO` until verified.** | **Mostly TODO.** |
| `document_format` | enum \| `TODO` | `html` \| `pdf` \| `hwp` \| `hwpx` \| `xlsx` \| `xls` \| `mixed`. | TODO until inspected. |
| `update_frequency` | enum \| `TODO` | `monthly` \| `quarterly` \| `irregular`. **[ASSUMPTION]** most agencies publish monthly or quarterly; confirm per agency. | TODO until inspected. |
| `crawl_difficulty` | enum | `low` (static HTML/attachment list) \| `medium` (paging/detail-follow needed) \| `high` (JS render / login / captcha / inline table). Initial guess allowed; refine after inspection. | Estimated. |
| `notes` | text | Anything special: per-일반구 publication, mixed formats, scanned PDFs, robots.txt constraints, etc. | Free text. |

Optional/derived fields (to align with existing code so the registry can later be lifted into `agencies.py` without redesign):

| Field | Description |
|---|---|
| `adapter` | Maps to an existing adapter value (§2) or `*_required` placeholder. |
| `follow_detail` | Boolean — whether attachments live on a detail page, mirroring `followDetail` in v1. |
| `page_param` / `page_unit_param` | Paging query parameters, mirroring v1's `pageParam` / `pageUnitParam`. |
| `verified_at` | Date the source was last verified by a human. Empty until verified. |
| `verified_by` | Who verified it. |

## 4. Registry skeleton (URLs intentionally TODO)

The registry is maintained as a structured table per region. Below is the **shape**; unverified rows remain `TODO`. We do **not** fabricate URLs.

### 4.1 Gyeonggi-do (64 entries)

| organization_name | jurisdiction_type | council_or_admin | source_url | document_format | crawl_difficulty | adapter | notes |
|---|---|---|---|---|---|---|---|
| 경기도청 | province | admin | `TODO` | `TODO` | medium | `gyeonggi_admin_required` | Province-level top office. |
| 경기도의회 | province | council | `https://www.ggc.go.kr/site/main/disclosureinfo/ParliaOper/duty/list?sortOrder=DT_USE_DT&listType=list` | xlsx/xls/pdf | medium | `council_attachment_board` | Verified in code. |
| 수원시청 | si | admin | `https://www.suwon.go.kr/web/board/BD_board.list.do?bbsCd=1179` | pdf/xls/xlsx | medium | `attachment_board` | Verified in code. |
| 수원시의회 | si | council | `https://council.suwon.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd=` | xls/xlsx/pdf | medium | `council_attachment_board` | Verified in code. |
| 성남시청 | si | admin | `https://www.seongnam.go.kr/city/1000199/30218/bbsList.do` | hwpx/xlsx/xls/pdf | medium | `attachment_board` | Verified in code; HWPX extraction supported. |
| 평택시청 | si | admin | `https://www.pyeongtaek.go.kr/pyeongtaek/board/post/list.do?bcIdx=264&mid=0110000000` | xls/xlsx/pdf | medium | `attachment_board` | Verified in code; `boardViewRenewal` detail links and `yhLib.file.download` attachments. |
| 의정부시청 | si | admin | `https://www.ui4u.go.kr/portal/bbs/list.do?mId=0114010300&ptIdx=25` | xlsx/xls/pdf | medium | `attachment_board` | Verified in code; extra list URLs cover mayor/deputy/other tabs. |
| 동두천시청 | si | admin | `https://www.ddc.go.kr/ddc/selectBbsNttList.do?bbsNo=38&key=122` | xlsx/xls/pdf | medium | `attachment_board` | Verified in code. |
| 안산시청 | si | admin | `https://www.ansan.go.kr/www/common/bbs/selectPageListBbs.do?bbs_code=B0471` | xls/xlsx/pdf | medium | `attachment_board` | Verified in code. |
| 부천시청 | si | admin | `https://www.bucheon.go.kr/site/program/board/basicboard/list?boardid=1192347&boardtypeid=26716&menuid=148004005002` | xlsx/xls/pdf/hwpx | medium | `attachment_board` | Verified in code. |
| 고양시청 | si | admin | `https://www.goyang.go.kr/www/publict/ntt/BD_selectPublictNttList.do?q_publictClCode=3062&q_searchKeyTy=1001&q_searchVal=%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84` | xlsx/xls/pdf | low | `attachment_board` | Verified in code; direct download list. |
| 오산시청 | si | admin | `https://www.osan.go.kr/portal/bbs/list.do?ptIdx=176&mId=0203010000` | pdf/xls/xlsx | medium | `attachment_board` | Verified in code; `goTo.view` detail links and eGov file downloads. |
| 의왕시청 | si | admin | `https://www.uiwang.go.kr/UWKOROPEN0210` | xlsx/xls/pdf | medium | `attachment_board` | Verified in code; same-board numeric detail URLs. |
| 안성시청 | si | admin | `https://www.anseong.go.kr/portal/businessExpense/list.do?mId=0402050000` | xlsx/xls/pdf | low | `attachment_board` | Verified in code; inline `data-column` download table. |
| 과천시청 | si | admin | `https://www.gccity.go.kr/portal/bbs/list.do?ptIdx=225&mId=0203080000` | xlsx/xls/pdf | medium | `attachment_board` | Verified in code. |
| 광주시청 | si | admin | `https://www.gjcity.go.kr/portal/bbs/list.do?mId=0311000000&ptIdx=53` | xlsx/xls/pdf | medium | `attachment_board` | Verified in code. |
| 가평군청 | gun | admin | `https://www.gp.go.kr/portal/selectBbsNttList.do?bbsNo=78&key=454` | pdf/xlsx/xls | medium | `attachment_board` | Verified in code. |
| 동두천시의회 | si | council | `https://council.ddc.go.kr/kr/news/bbsCost.do` | xlsx/xls/pdf | medium | `council_attachment_board` | Verified in code. |
| 안성시의회 | si | council | `https://www.anseongcl.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd=` | xlsx/xls/pdf | medium | `council_attachment_board` | Verified in code. |
| 김포시의회 | si | council | `https://gimpocouncil.go.kr/cnts/bbs/infoList.php?bbsCd=act&bbsSubCd=act0702` | xlsx/xls/pdf | medium | `council_attachment_board` | Verified in code; uses configured `fileDownLoad` path. |
| 화성시의회 | si | council | `https://council.hscity.go.kr/cnts/bbs/boardList.php?bbsCd=cns&bbsSubCd=cns08` | xlsx/xls/pdf | medium | `council_attachment_board` | Verified in code; uses configured `fileDownLoad` path. |
| 여주시의회 | si | council | `https://www.yeojucouncil.go.kr/kr/costBBS.do` | xls/xlsx/pdf | medium | `council_attachment_board` | Verified in code. |
| … (remaining 경기 entries) | … | … | `TODO` or verified URL in code | `TODO` or file kinds in code | … | `*_required` or concrete adapter | Code-generated registry is the source of truth for the full row set. |

> Full row set = 2 (province office+council) + 31×2 (시·군 office+council) = **64 rows**. Verified rows are listed in code; unverified rows keep `source_url = TODO`/`adapter_required`.

### 4.2 Incheon (22 entries)

| organization_name | jurisdiction_type | council_or_admin | source_url | document_format | crawl_difficulty | adapter | notes |
|---|---|---|---|---|---|---|---|
| 인천광역시청 | metro_city | admin | `https://www.incheon.go.kr/open/OPEN010305` | pdf/xlsx/xls | medium | `attachment_board` | Verified in code. |
| 인천광역시의회 | metro_city | council | `https://www.icouncil.go.kr/main/participate/expense_office.jsp` | pdf | medium | `council_attachment_board` | Verified in code; extra list URL covers council expense page. |
| 인천광역시 중구청 | autonomous_gu | admin | `https://www.icjg.go.kr/krop0307c` | xlsx/xls/pdf | medium | `attachment_board` | Note: 중구 name collides with Seoul 중구 — disambiguate by region. |
| 인천광역시 중구의회 | autonomous_gu | council | `https://www.icjg.go.kr/council/cnac04b` | xlsx/xls/pdf | medium | `council_attachment_board` | Verified in code. |
| 인천광역시 동구청 | autonomous_gu | admin | `https://www.icdonggu.go.kr/main/bbs/bbsMsgList.do?bcd=notice&keyfield=title&keyword=%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84` | xlsx/xls/pdf | medium | `attachment_board` | Verified in code; official notice search result board. |
| 인천광역시 미추홀구청 | autonomous_gu | admin | `https://www.michuhol.go.kr/main/board/list.do?board_code=business_promotion&dept_sq=333&page=1&srchCate=&year=` | xlsx/xls/pdf | medium | `attachment_board` | Verified in code. |
| 인천광역시 연수구청 | autonomous_gu | admin | `https://www.yeonsu.go.kr/main/administration/open_info/charge.asp` | xlsx/xls/pdf | medium | `attachment_board` | Verified in code. |
| 인천광역시 부평구청 | autonomous_gu | admin | `https://www.icbp.go.kr/main/bbs/bbsMsgList.do?bcd=cost` | xlsx/xls/pdf | medium | `attachment_board` | Verified in code. |
| 인천광역시 남동구청 | autonomous_gu | admin | `https://biz.namdong.go.kr/main/bbs/bbsMsgList.do?bcd=disclosure` | xlsx/xls/pdf | medium | `attachment_board` | Verified in code. |
| 인천광역시 남동구의회 | autonomous_gu | council | `https://council.namdong.go.kr/kr/data/bbsBreakdown.do` | xlsx/xls/pdf | medium | `council_attachment_board` | Verified in code. |
| 인천광역시 강화군청 | gun | admin | `https://www.ganghwa.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=operation` | xlsx/xls/pdf | medium | `attachment_board` | Verified in code. |
| 인천광역시 옹진군청 | gun | admin | `https://www.ongjin.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=opendata1` | xlsx/xls/pdf | low | `attachment_board` | Verified in code; direct attachment list. |
| … (remaining 인천 entries) | … | … | `TODO` or verified URL in code | `TODO` or file kinds in code | … | `*_required` or concrete adapter | Code-generated registry is the source of truth for the full row set. |

> Full row set = 2 (metro office+council) + 10×2 (군·구 office+council) = **22 rows**. Verified rows are listed in code; unverified rows keep `source_url = TODO`/`adapter_required`.

### 4.3 Name-collision note **[FACT/RISK]**

중구 and 동구 exist in both Seoul and Incheon; 서구 exists in Incheon (and other metros). The agency natural key includes `gov_tier`, `branch`, `parent_region`, and `sub_region` (`agencies UNIQUE (gov_tier, branch, parent_region, sub_region)`).

## 5. Where candidate URLs may come from (verification inputs, not auto-fill)

These are **leads to verify by hand**, not values to write into the registry automatically:

- The official homepage of each agency (the province/metro/city/county/district site), then locate its 정보공개 / 업무추진비 / 행정정보공개 board.
- 경기도 / 인천 open-data portals, if they aggregate 업무추진비 (to be checked; **[ASSUMPTION]** coverage is partial).
- The same publication pattern Seoul councils use (`council.<domain>` style boards), which **[ASSUMPTION]** may recur for Gyeonggi/Incheon councils but must not be assumed identical.

> A lead is only promoted to a real `source_url` after passing §6 verification. Until then it stays `TODO`.

## 6. Source verification procedure

For each agency, a human (or human-supervised step) performs the following before the entry leaves `TODO`/`*_required` state:

1. **Locate** the 업무추진비 disclosure board on the agency's official site.
2. **Confirm authority**: the page is the agency's own official domain, and the data is the legally-mandated 업무추진비 disclosure (집행일시/장소/목적/대상/금액/결재방법) — matching the fields in [docs/LEGAL_PRIVACY.md](../../LEGAL_PRIVACY.md) §"의무 공개 항목".
3. **Confirm license/attribution**: the data is 공공누리 제1유형 (or equivalent legally-mandated public disclosure). Record the exact attribution string to reproduce in the footer/legal page.
4. **Record format**: note `document_format` (html/pdf/hwp/hwpx/xlsx/xls/mixed) and whether PDFs are text-based or scanned (affects extraction path — see [03_BACKFILL_AND_PIPELINE_PLAN.md](03_BACKFILL_AND_PIPELINE_PLAN.md)).
5. **Record frequency & window**: how far back the board goes (needed to judge whether the 24-month backfill is achievable) and how often it updates.
6. **Record access constraints**: robots.txt, login/captcha, JS rendering, paging parameters, rate limits.
7. **Set `crawl_difficulty`** based on 4–6.
8. **Capture a sample**: save 1–2 example documents for the dry-run sample set (no production write).
9. **Stamp** `verified_at` + `verified_by`. Only now may `source_url`/`adapter` be filled and the `*_required` placeholder removed.

A source that fails any of 1–3 is **not** added; instead it becomes a tracked open item.

## 7. Registry completion definition

The source registry for v2 is "complete" when:

- All 86 new agencies have a registry entry (even if some remain `*_required`).
- Every entry that will be crawled has a `verified_at` stamp and a non-`TODO` `source_url`, `document_format`, and `crawl_difficulty`.
- Any agency that genuinely does not publish online (or only on paper / via 정보공개청구) is explicitly marked as such in `notes`, rather than left ambiguous.
- The verified-vs-pending count is summarized so the rollout plan can decide which batches are runnable.

See [07_ACCEPTANCE_CRITERIA.md](07_ACCEPTANCE_CRITERIA.md) §"Source registry completion".

## 8. Relationship to existing code (no code change now)

When (later, in a separate implementation stage) these entries are lifted into `agencies.py`:

- Each entry becomes an `Agency(...)` with a `source_pattern` jsonb mirroring §3's `adapter`/`follow_detail`/`page_param` fields.
- The `assert len(SEOUL_AGENCIES) == 52` invariant stays; new regions get their own builder functions and their own count asserts (e.g. `assert len(GYEONGGI_AGENCIES) == 64`, `assert len(INCHEON_AGENCIES) == 22`).
- This document does **not** perform that lift; it only ensures the registry is shaped so the lift is mechanical.
