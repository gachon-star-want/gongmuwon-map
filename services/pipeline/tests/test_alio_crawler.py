from __future__ import annotations

from datetime import date

import httpx
import pytest

from public_officer_pipeline.agencies import agency_uuid
from public_officer_pipeline.crawler.alio import AlioItemDisclosureCrawler
from public_officer_pipeline.models import Agency, ExpansionPhase, GovBranch, GovTier, JurisdictionType
from public_officer_pipeline.source_pattern import AlioItemDisclosurePattern


@pytest.mark.asyncio
async def test_alio_item_disclosure_crawler_lists_and_fetches_matching_attachment() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/itemOrganListJung.json"):
            return httpx.Response(
                200,
                json={
                    "data": {
                        "organList": [
                            {
                                "apbaNa": "게임물관리위원회",
                                "disclosureNo": "2026041303156569",
                                "files": (
                                    "101@기관장 업무추진비 집행내역(2025년).xlsx|"
                                    "102@기관장 업무추진비 집행내역(2024년).xlsx"
                                ),
                            }
                        ]
                    }
                },
            )
        if request.url.path.endswith("/file.json"):
            assert request.url.params["f"] == "101"
            assert request.url.params["d"] == "2026041303156569"
            return httpx.Response(200, content=b"spreadsheet-bytes")
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://www.alio.go.kr")
    agency = Agency(
        id=agency_uuid("p3:C0402:게임물관리위원회"),
        name="게임물관리위원회",
        short_name="게임물관리위원회",
        gov_tier=GovTier.PUBLIC,
        branch=GovBranch.PUBLIC,
        jurisdiction_type=JurisdictionType.PUBLIC_INSTITUTION,
        expansion_phase=ExpansionPhase.P3,
        parent_region="문화체육관광부",
        source_pattern={},
    )
    pattern = AlioItemDisclosurePattern(
        adapter="alio_item_disclosure",
        alioAgencyName="게임물관리위원회",
    )
    crawler = AlioItemDisclosureCrawler(agency=agency, client=client, source_pattern=pattern)

    refs = await crawler.list_posts(since=date(2025, 6, 1), limit_pages=2)

    assert len(refs) == 1
    assert refs[0].file_kind == "xlsx"
    assert refs[0].published_at.isoformat() == "2026-04-13"
    assert "f=101" in refs[0].url
    assert "d=2026041303156569" in refs[0].url

    detail = await crawler.fetch_post(refs[0])

    assert detail.content_bytes == b"spreadsheet-bytes"
    assert detail.file_kind == "xlsx"
