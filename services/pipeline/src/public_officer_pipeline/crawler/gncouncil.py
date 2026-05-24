from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from public_officer_pipeline.agencies import SEOUL_AGENCIES
from public_officer_pipeline.models import Agency, PostDetail, PostRef


DEFAULT_LIST_URL = "https://www.gncouncil.go.kr/kr/noticeBBS.do"
DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
SUPPORTED_FILE_KINDS = {"pdf", "xlsx"}
EXPENSE_KEYWORDS = ("업무추진비", "업추비")


class CouncilAttachmentCrawler:
    def __init__(self, agency: Agency | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.agency = agency or next(item for item in SEOUL_AGENCIES if item.short_name == "강남구의회")
        self.list_url = str(self.agency.source_pattern.get("listUrl") or DEFAULT_LIST_URL)
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
            response = await self._client.get(self.list_url, params={"page": page})
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
            title = _normalize_spaces(cells[1].text(separator=" ", strip=True))
            if not _looks_like_expense(title):
                continue
            published_at = _find_date(cells)
            for download in cells[5].css('a[href*="/bbs/download.do"]'):
                filename = _filename_from_download_link(download)
                href = download.attributes.get("href", "")
                file_kind = _file_kind(filename)
                if (
                    not href
                    or file_kind not in SUPPORTED_FILE_KINDS
                    or not _download_looks_like_expense(title=title, filename=filename)
                ):
                    continue
                refs.append(
                    PostRef(
                        agency_id=self.agency.id,
                        url=urljoin(self.list_url, href),
                        title=f"{title} - {filename}",
                        published_at=published_at,
                        department_name=_department_from_filename(filename, self.agency.short_name),
                        file_kind=file_kind,
                    )
                )
        return refs


class GangnamCouncilCrawler(CouncilAttachmentCrawler):
    pass


def _filename_from_download_link(download) -> str:
    candidates = [
        download.text(separator=" ", strip=True),
        download.attributes.get("title", ""),
    ]
    image = download.css_first("img")
    if image:
        candidates.append(image.attributes.get("alt", ""))
    for candidate in candidates:
        normalized = _normalize_spaces(candidate)
        if not normalized:
            continue
        if "파일 내려받기" in normalized:
            normalized = normalized.replace("파일 내려받기", "")
        return normalized.strip(" '\"")
    return ""


def _department_from_filename(filename: str, agency_short_name: str = "강남구의회") -> str:
    if "사무국" in filename:
        return f"{agency_short_name} 사무국"
    if "의장단" in filename:
        return f"{agency_short_name} 의장단"
    if "의장" in filename:
        return f"{agency_short_name} 의장"
    if "부의장" in filename:
        return f"{agency_short_name} 부의장"
    if "위원장" in filename:
        return f"{agency_short_name} 위원장"
    if "교섭단체" in filename:
        return f"{agency_short_name} 교섭단체"
    return agency_short_name


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _find_date(cells) -> date | None:
    for cell in cells:
        parsed = _parse_date(cell.text(separator=" ", strip=True))
        if parsed:
            return parsed
    return None


def _file_kind(filename: str) -> str:
    lowered = filename.lower()
    for file_kind in SUPPORTED_FILE_KINDS:
        if lowered.endswith(f".{file_kind}"):
            return file_kind
    return ""


def _looks_like_expense(value: str) -> bool:
    return any(keyword in value for keyword in EXPENSE_KEYWORDS)


def _download_looks_like_expense(*, title: str, filename: str) -> bool:
    if filename:
        return _looks_like_expense(filename)
    return _looks_like_expense(title)


def _normalize_spaces(value: str) -> str:
    return " ".join(value.split())
