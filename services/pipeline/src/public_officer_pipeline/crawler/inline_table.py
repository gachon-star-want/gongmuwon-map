from __future__ import annotations

from typing import Any
from datetime import date
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from public_officer_pipeline.agencies import SEOUL_AGENCIES
from public_officer_pipeline.models import Agency, PostDetail, PostRef
from public_officer_pipeline.artifact import artifact_from_response, post_detail_from_artifact
from public_officer_pipeline.http_client import create_http_client
from public_officer_pipeline.source_pattern import InlineExpenseTablePattern, parse_source_pattern


DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class InlineExpenseTableCrawler:
    def __init__(
        self,
        agency: Agency | None = None,
        client: Any | None = None,
        source_pattern: InlineExpenseTablePattern | None = None,
    ) -> None:
        self.agency = agency or next(item for item in SEOUL_AGENCIES if item.short_name == "은평구청")
        pattern = source_pattern or parse_source_pattern(self.agency)
        if not isinstance(pattern, InlineExpenseTablePattern):
            raise ValueError("InlineExpenseTableCrawler requires an inline_expense_table source pattern")
        self.list_url = pattern.listUrl
        self.rows_per_page = pattern.rowsPerPage
        self.page_param = pattern.pageParam
        self.page_unit_param = pattern.pageUnitParam
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
        return post_detail_from_artifact(artifact_from_response(ref, response))

    def _url_for_page(self, page: int) -> str:
        parts = urlsplit(self.list_url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query[self.page_param] = str(page)
        query[self.page_unit_param] = str(self.rows_per_page)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
