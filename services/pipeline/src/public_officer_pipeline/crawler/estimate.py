from __future__ import annotations

import hashlib
import math
import re
from datetime import date, datetime, timezone
from urllib.parse import urlencode, urlsplit, urlunsplit

import httpx
from selectolax.parser import HTMLParser

from public_officer_pipeline.agencies import SEOUL_AGENCIES
from public_officer_pipeline.models import Agency, PostDetail, PostRef


DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
COUNT_RE = re.compile(r"건수\s*:\s*([\d,]+)")


class EstimateListCrawler:
    def __init__(self, agency: Agency | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.agency = agency or next(item for item in SEOUL_AGENCIES if item.short_name == "관악구청")
        pattern = self.agency.source_pattern
        self.list_url = str(pattern.get("listUrl") or "https://www.gwanak.go.kr/site/gwanak/estimate/estimateList.do")
        self.rows_per_page = int(pattern.get("rowsPerPage") or 10)
        self._client = client or httpx.AsyncClient(
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
        html = response.text
        return PostDetail(
            **ref.model_dump(),
            html=html,
            fetched_at=datetime.now(timezone.utc),
            hash_sha256=hashlib.sha256(html.encode("utf-8")).hexdigest(),
        )

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
