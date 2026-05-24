from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from public_officer_pipeline.agencies import SEOUL_AGENCIES
from public_officer_pipeline.models import Agency, PostDetail, PostRef


DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class InlineExpenseTableCrawler:
    def __init__(self, agency: Agency | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.agency = agency or next(item for item in SEOUL_AGENCIES if item.short_name == "은평구청")
        pattern = self.agency.source_pattern
        self.list_url = str(pattern["listUrl"])
        self.rows_per_page = int(pattern.get("rowsPerPage") or 100)
        self.page_param = str(pattern.get("pageParam") or "pageIndex")
        self.page_unit_param = str(pattern.get("pageUnitParam") or "pageUnit")
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
        return [
            PostRef(
                agency_id=self.agency.id,
                url=self._url_for_page(page),
                title=f"{self.agency.short_name} 업무추진비 공개 {since.isoformat()} page {page}",
                published_at=None,
                department_name=self.agency.short_name,
                file_kind="html",
            )
            for page in range(1, limit_pages + 1)
        ]

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

    def _url_for_page(self, page: int) -> str:
        parts = urlsplit(self.list_url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query[self.page_param] = str(page)
        query[self.page_unit_param] = str(self.rows_per_page)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
