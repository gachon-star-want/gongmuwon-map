from __future__ import annotations

import re
from typing import Any
from datetime import date
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from public_officer_pipeline.models import Agency, PostDetail, PostRef, SEOUL_CITY_HALL_AGENCY_ID
from public_officer_pipeline.http_client import create_http_client
from public_officer_pipeline.artifact import artifact_from_response, post_detail_from_artifact
from public_officer_pipeline.source_pattern import (
    SeoulOpenGovPattern,
    parse_source_pattern,
)


LIST_URL = "https://opengov.seoul.go.kr/expense/list"
DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
EXPENSE_LINK_RE = re.compile(r"/expense/(\d+)(?:\b|$)")
DATE_RE = re.compile(r"(20\d{2})[.-](\d{1,2})[.-](\d{1,2})")


class SeoulOpenGovCrawler:
    agency_id = SEOUL_CITY_HALL_AGENCY_ID

    def __init__(
        self,
        agency: Agency | None = None,
        client: Any | None = None,
        source_pattern: SeoulOpenGovPattern | None = None,
    ) -> None:
        self.agency = agency or Agency()
        pattern = source_pattern or parse_source_pattern(self.agency)
        if not isinstance(pattern, SeoulOpenGovPattern):
            raise ValueError("SeoulOpenGovCrawler requires a seoul_opengov source pattern")
        self.search_keyword = pattern.searchKeyword
        title_includes = pattern.titleIncludes or [self.search_keyword]
        self.title_includes = [str(item) for item in title_includes if str(item).strip()]
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
        posts: dict[str, PostRef] = {}
        for page in range(limit_pages):
            response = await self._client.get(
                LIST_URL,
                params={
                    "items_per_page": 50,
                    "page": page,
                    "searchKeyword": self.search_keyword,
                    "sortField": "reg_date",
                    "sortOrder": "desc",
                    "ym[year]": "all",
                    "ym[month]": "all",
                },
            )
            response.raise_for_status()
            for post in self._parse_list(response.text):
                if post.published_at and post.published_at < since:
                    continue
                posts[post.url] = post
        return list(posts.values())

    async def fetch_post(self, ref: PostRef) -> PostDetail:
        response = await self._client.get(ref.url)
        response.raise_for_status()
        return post_detail_from_artifact(artifact_from_response(ref, response))

    def _parse_list(self, html: str) -> list[PostRef]:
        tree = HTMLParser(html)
        refs: list[PostRef] = []
        seen: set[str] = set()
        for anchor in tree.css("a[href]"):
            href = anchor.attributes.get("href", "")
            if not EXPENSE_LINK_RE.search(href):
                continue
            url = urljoin(LIST_URL, href.split("?")[0])
            if url in seen:
                continue
            title = " ".join(anchor.text(separator=" ", strip=True).split())
            if "업무추진비" not in title:
                continue
            if self.title_includes and not all(token in title for token in self.title_includes):
                continue
            row_text = " ".join((anchor.parent.text(separator=" ", strip=True) if anchor.parent else title).split())
            refs.append(
                PostRef(
                    agency_id=self.agency.id,
                    url=url,
                    title=title,
                    published_at=_extract_date(row_text),
                )
            )
            seen.add(url)
        return refs


def _extract_date(text: str) -> date | None:
    match = DATE_RE.search(text)
    if not match:
        return None
    year, month, day = (int(part) for part in match.groups())
    return date(year, month, day)
