from __future__ import annotations

import math
import re
from datetime import date
from urllib.parse import urlencode, urlsplit, urlunsplit
from typing import Any

import httpx
from selectolax.parser import HTMLParser

from public_officer_pipeline.agencies import SEOUL_AGENCIES
from public_officer_pipeline.models import Agency, PostDetail, PostRef
from public_officer_pipeline.artifact import artifact_from_response, post_detail_from_artifact
from public_officer_pipeline.http_client import create_http_client
from public_officer_pipeline.source_pattern import (
    EstimateListPattern,
    parse_source_pattern,
)


DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
COUNT_RE = re.compile(r"건수\s*:\s*([\d,]+)")


class EstimateListCrawler:
    def __init__(
        self,
        agency: Agency | None = None,
        client: Any | None = None,
        source_pattern: EstimateListPattern | None = None,
    ) -> None:
        self.agency = agency or next(item for item in SEOUL_AGENCIES if item.short_name == "관악구청")
        pattern = source_pattern or parse_source_pattern(self.agency)
        if not isinstance(pattern, EstimateListPattern):
            raise ValueError("EstimateListCrawler requires an estimate_list_html source pattern")
        self.list_url = pattern.listUrl
        self.rows_per_page = pattern.rowsPerPage
        self._client = client or create_http_client(
            timeout=DEFAULT_TIMEOUT,
            headers={
                "User-Agent": (
                    "PublicOfficerMapBot/0.1 "
                    "(operator: wylee0806@naver.com; public-interest archive)"
                )
            },
            follow_redirects=True,
        )
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def list_posts(self, since: date, limit_pages: int = 3) -> list[PostRef]:
        refs: list[PostRef] = []
        first_url = self._url_for_page(1, since=since)
        response = await self._client.get(first_url)
        response.raise_for_status()
        page_count = min(limit_pages, _page_count(response.text, self.rows_per_page) or limit_pages)
        refs.append(self._ref_for_page(1, first_url, since))
        for page in range(2, page_count + 1):
            refs.append(self._ref_for_page(page, self._url_for_page(page, since=since), since))
        return refs

    async def fetch_post(self, ref: PostRef) -> PostDetail:
        response = await self._client.get(ref.url)
        response.raise_for_status()
        return post_detail_from_artifact(artifact_from_response(ref, response))

    def _ref_for_page(self, page: int, url: str, since: date) -> PostRef:
        return PostRef(
            agency_id=self.agency.id,
            url=url,
            title=f"{self.agency.short_name} 업무추진비 공개 {since.isoformat()} page {page}",
            published_at=None,
            department_name=self.agency.short_name,
            file_kind="html",
        )

    def _url_for_page(self, page: int, *, since: date) -> str:
        return _url_with_query(
            self.list_url,
            {
                "pageIndex": str(page),
                "searchCondition3": since.isoformat(),
                "searchCondition4": date.today().isoformat(),
            },
        )


def _page_count(html: str, rows_per_page: int) -> int:
    tree = HTMLParser(html)
    text = tree.text(separator=" ", strip=True)
    match = COUNT_RE.search(text)
    if not match:
        return 0
    count = int(match.group(1).replace(",", ""))
    return math.ceil(count / rows_per_page)


def _url_with_query(url: str, params: dict[str, str]) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(params), parts.fragment))
