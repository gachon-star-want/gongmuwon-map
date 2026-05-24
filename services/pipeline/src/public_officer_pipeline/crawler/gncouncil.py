from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from public_officer_pipeline.agencies import SEOUL_AGENCIES
from public_officer_pipeline.models import Agency, PostDetail, PostRef


LIST_URL = "https://www.gncouncil.go.kr/kr/noticeBBS.do"
DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class GangnamCouncilCrawler:
    def __init__(self, agency: Agency | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.agency = agency or next(item for item in SEOUL_AGENCIES if item.short_name == "강남구의회")
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
            response = await self._client.get(LIST_URL, params={"page": page})
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
        return PostDetail(
            **ref.model_dump(),
            html="",
            content_bytes=content,
            fetched_at=datetime.now(timezone.utc),
            hash_sha256=hashlib.sha256(content).hexdigest(),
        )

    def _parse_list(self, html: str) -> list[PostRef]:
        tree = HTMLParser(html)
        refs: list[PostRef] = []
        for row in tree.css("tbody tr"):
            cells = row.css("td")
            if len(cells) < 6:
                continue
            title = " ".join(cells[1].text(separator=" ", strip=True).split())
            if "업무추진비" not in title:
                continue
            published_at = _parse_date(cells[3].text(separator=" ", strip=True))
            for download in cells[5].css('a[href*="/bbs/download.do"]'):
                filename = " ".join(download.text(separator=" ", strip=True).split())
                href = download.attributes.get("href", "")
                if not href or ".pdf" not in filename.lower():
                    continue
                refs.append(
                    PostRef(
                        agency_id=self.agency.id,
                        url=urljoin(LIST_URL, href),
                        title=f"{title} - {filename}",
                        published_at=published_at,
                        department_name=_department_from_filename(filename),
                        file_kind="pdf",
                    )
                )
        return refs


def _department_from_filename(filename: str) -> str:
    if "의장" in filename:
        return "강남구의회 의장"
    if "부의장" in filename:
        return "강남구의회 부의장"
    if "위원장" in filename:
        return "강남구의회 위원장"
    if "교섭단체" in filename:
        return "강남구의회 교섭단체"
    return "강남구의회"


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None
