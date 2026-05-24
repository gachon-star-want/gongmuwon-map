from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from email.message import Message
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from public_officer_pipeline.agencies import SEOUL_AGENCIES
from public_officer_pipeline.models import Agency, PostDetail, PostRef


LIST_URL = "https://www.gangnam.go.kr/board/B_000673/list.do"
DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class GangnamExpenseCrawler:
    def __init__(self, agency: Agency | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.agency = agency or next(item for item in SEOUL_AGENCIES if item.short_name == "강남구청")
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
        refs: dict[str, PostRef] = {}
        for page in range(1, limit_pages + 1):
            response = await self._client.get(
                LIST_URL,
                params={"mid": "ID05_04200502", "pgno": page, "lists": 10},
            )
            response.raise_for_status()
            for ref in self._parse_list(response.text):
                if ref.published_at and ref.published_at < since:
                    continue
                refs[ref.url] = ref
        return list(refs.values())

    async def fetch_post(self, ref: PostRef) -> PostDetail:
        response = await self._client.get(ref.url)
        response.raise_for_status()
        content = response.content
        data = ref.model_dump()
        data["file_kind"] = _file_kind(response.headers.get("content-disposition", ""))
        return PostDetail(
            **data,
            html="",
            content_bytes=content,
            fetched_at=datetime.now(timezone.utc),
            hash_sha256=hashlib.sha256(content).hexdigest(),
        )

    def _parse_list(self, html: str) -> list[PostRef]:
        tree = HTMLParser(html)
        refs: list[PostRef] = []
        for row in tree.css("tr.grid-item"):
            cells = row.css("td")
            if len(cells) < 5:
                continue
            title = " ".join(cells[1].text(separator=" ", strip=True).split())
            if "업무추진비" not in title:
                continue
            download = cells[2].css_first('a[href*="/download.do"]')
            if not download:
                continue
            href = download.attributes.get("href")
            if not href:
                continue
            department = " ".join(cells[3].text(separator=" ", strip=True).split())
            published_at = _parse_date(cells[4].text(separator=" ", strip=True))
            refs.append(
                PostRef(
                    agency_id=self.agency.id,
                    url=urljoin(LIST_URL, href),
                    title=f"{title} - {department}" if department else title,
                    published_at=published_at,
                    department_name=department or self.agency.short_name,
                    file_kind="xlsx",
                )
            )
        return refs


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _file_kind(content_disposition: str) -> str:
    message = Message()
    message["content-disposition"] = content_disposition
    filename = message.get_filename("") or ""
    if filename.lower().endswith(".xlsx"):
        return "xlsx"
    if filename.lower().endswith(".xls"):
        return "xls"
    return "xlsx"
