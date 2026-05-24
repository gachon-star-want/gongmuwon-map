from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timezone
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from public_officer_pipeline.models import PostDetail, PostRef, SEOUL_CITY_HALL_AGENCY_ID


LIST_URL = "https://opengov.seoul.go.kr/expense/list"
DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
EXPENSE_LINK_RE = re.compile(r"/expense/(\d+)(?:\b|$)")
DATE_RE = re.compile(r"(20\d{2})[.-](\d{1,2})[.-](\d{1,2})")


class SeoulOpenGovCrawler:
    agency_id = SEOUL_CITY_HALL_AGENCY_ID

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
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
        posts: dict[str, PostRef] = {}
        for page in range(limit_pages):
            response = await self._client.get(
                LIST_URL,
                params={
                    "items_per_page": 50,
                    "page": page,
                    "searchKeyword": "서울시본청",
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
        content = response.text
        return PostDetail(
            **ref.model_dump(),
            html=content,
            fetched_at=datetime.now(timezone.utc),
            hash_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        )

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
            if "업무추진비" not in title or "서울시본청" not in title:
                continue
            row_text = " ".join((anchor.parent.text(separator=" ", strip=True) if anchor.parent else title).split())
            refs.append(
                PostRef(
                    agency_id=self.agency_id,
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
