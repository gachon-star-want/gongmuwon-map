from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timezone
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx
from selectolax.parser import HTMLParser

from public_officer_pipeline.agencies import SEOUL_AGENCIES
from public_officer_pipeline.models import Agency, PostDetail, PostRef


DEFAULT_LIST_URL = "https://www.gncouncil.go.kr/kr/noticeBBS.do"
DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
SUPPORTED_FILE_KINDS = {"pdf", "xls", "xlsx"}
EXPENSE_KEYWORDS = ("업무추진비", "업추비", "시책추진비")
DOWNLOAD_HREF_PARTS = (
    "/bbs/download.do",
    "/bbs/download?",
    "/bbsAttachDownload.do",
    "bbs_process?reform=download",
    "/Mboard/download.html",
    "/FileDown.do",
    "/gtb_download.php",
    "/file/download/",
    "downloadBbsFile.do",
    "downloadBbsFileStr.do",
    "/common/board/Download.do",
    "/component/file/ND_fileDownload.do",
    "/comm/getFile",
)
DATE_RE = re.compile(r"(20\d{2})[.-](\d{1,2})[.-](\d{1,2})")


class CouncilAttachmentCrawler:
    def __init__(self, agency: Agency | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.agency = agency or next(item for item in SEOUL_AGENCIES if item.short_name == "강남구의회")
        pattern = self.agency.source_pattern
        self.list_url = str(pattern.get("listUrl") or DEFAULT_LIST_URL)
        self.follow_detail = bool(pattern.get("followDetail"))
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
            response = await self._client.get(_url_with_page(self.list_url, page))
            response.raise_for_status()
            for ref in self._parse_list(_response_text(response)):
                if ref.published_at and ref.published_at < since:
                    continue
                refs[ref.url] = ref
            if self.follow_detail:
                for detail in self._parse_detail_links(_response_text(response)):
                    if detail.published_at and detail.published_at < since:
                        continue
                    detail_response = await self._client.get(detail.url)
                    detail_response.raise_for_status()
                    for ref in self._parse_detail_downloads(_response_text(detail_response), detail):
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
            if len(cells) < 4:
                continue
            title = _normalize_spaces(cells[1].text(separator=" ", strip=True))
            if not _looks_like_expense(title):
                continue
            published_at = _find_date(cells)
            for download in cells[-1].css("a[href]"):
                filename = _filename_from_download_link(download)
                href = download.attributes.get("href", "")
                file_kind = _file_kind(filename)
                if (
                    not href
                    or not _is_download_href(href)
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
                        department_name=_best_department(
                            _department_from_filename(filename, self.agency.short_name),
                            _department_from_filename(title, self.agency.short_name),
                            _department_from_cells(cells, self.agency.short_name),
                            self.agency.short_name,
                        ),
                        file_kind=file_kind,
                    )
                )
        return refs

    def _parse_detail_links(self, html: str) -> list[PostRef]:
        tree = HTMLParser(html)
        refs: list[PostRef] = []
        for row in tree.css("tbody tr"):
            cells = row.css("td")
            if len(cells) < 4:
                continue
            title_cell = cells[1]
            title = _normalize_spaces(title_cell.text(separator=" ", strip=True))
            if not _looks_like_expense(title):
                continue
            anchor = title_cell.css_first("a[href]")
            if not anchor:
                continue
            script_title = re.search(r"wdigm_title\('(?P<title>[^']+)'\)", title)
            if script_title:
                title = script_title.group("title")
            href = anchor.attributes.get("href", "")
            onclick = anchor.attributes.get("onclick", "")
            bbs_view = re.search(r"doBbsFView\('(?P<cb_idx>[^']+)'\s*,\s*'(?P<bc_idx>[^']+)'", onclick)
            if bbs_view:
                href = (
                    "/site/yangcheon/ex/bbs/View.do"
                    f"?cbIdx={bbs_view.group('cb_idx')}&bcIdx={bbs_view.group('bc_idx')}"
                )
            if not href:
                continue
            refs.append(
                PostRef(
                    agency_id=self.agency.id,
                    url=urljoin(self.list_url, href),
                    title=title,
                    published_at=_find_date(cells),
                    department_name=_department_from_filename(title, self.agency.short_name),
                    file_kind="html",
                )
            )
        if refs:
            return refs
        seen: set[str] = set()
        for anchor in tree.css("a[href]"):
            title = _normalize_spaces(anchor.text(separator=" ", strip=True))
            if not _looks_like_expense(title):
                continue
            href = anchor.attributes.get("href", "")
            if not href or "view.do" not in href:
                continue
            url = urljoin(self.list_url, href)
            if url in seen:
                continue
            refs.append(
                PostRef(
                    agency_id=self.agency.id,
                    url=url,
                    title=title,
                    published_at=_parse_date(anchor.parent.text(separator=" ", strip=True)) if anchor.parent else None,
                    department_name=_department_from_filename(title, self.agency.short_name),
                    file_kind="html",
                )
            )
            seen.add(url)
        return refs

    def _parse_detail_downloads(self, html: str, detail: PostRef) -> list[PostRef]:
        tree = HTMLParser(html)
        refs: list[PostRef] = []
        for download in tree.css("a[href]"):
            href = download.attributes.get("href", "")
            if not href or not _is_download_href(href):
                continue
            filename = _filename_from_download_link(download)
            file_kind = _file_kind(filename)
            if (
                file_kind not in SUPPORTED_FILE_KINDS
                or not _download_looks_like_expense(title=detail.title, filename=filename)
            ):
                continue
            refs.append(
                PostRef(
                    agency_id=self.agency.id,
                    url=urljoin(detail.url, href),
                    title=f"{detail.title} - {filename}",
                    published_at=detail.published_at,
                    department_name=_best_department(
                        _department_from_filename(filename or detail.title, self.agency.short_name),
                        detail.department_name,
                        self.agency.short_name,
                    ),
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
    normalized_candidates = []
    for candidate in candidates:
        normalized = _normalize_spaces(candidate)
        if not normalized:
            continue
        if "파일 내려받기" in normalized:
            normalized = normalized.replace("파일 내려받기", "")
        normalized_candidates.append(normalized.strip(" '\""))
    for candidate in normalized_candidates:
        if _file_kind(candidate) or _looks_like_expense(candidate):
            return candidate
    if normalized_candidates:
        return normalized_candidates[0]
    return ""


def _department_from_filename(filename: str, agency_short_name: str = "강남구의회") -> str:
    if "사무국" in filename:
        return f"{agency_short_name} 사무국"
    if "의장단" in filename:
        return f"{agency_short_name} 의장단"
    if "부의장" in filename:
        return f"{agency_short_name} 부의장"
    if "의장" in filename:
        return f"{agency_short_name} 의장"
    if "위원장" in filename:
        return f"{agency_short_name} 위원장"
    if "교섭단체" in filename:
        return f"{agency_short_name} 교섭단체"
    parenthetical = re.search(r"업무추진비\((?P<department>[^)]+)\)", filename)
    if parenthetical:
        department = parenthetical.group("department").strip()
        if _looks_like_department_fragment(department):
            return f"{agency_short_name} {department}"
    parenthetical = re.search(r"\((?P<department>[^)]+)\)", filename)
    if parenthetical:
        department = parenthetical.group("department").strip()
        if _looks_like_department_fragment(department):
            return f"{agency_short_name} {department}"
    department_match = re.search(
        r"\d{1,2}월\s+(?P<department>[가-힣0-9]+(?:담당관|구청장|부구청장|국장|과|팀|국|동|소|센터|실))",
        filename,
    )
    if department_match:
        return f"{agency_short_name} {department_match.group('department')}"
    return agency_short_name


def _department_from_cells(cells, agency_short_name: str) -> str | None:
    for cell in cells[2:-1]:
        text = _normalize_spaces(cell.text(separator=" ", strip=True))
        if not text or DATE_RE.search(text) or re.fullmatch(r"\d+", text):
            continue
        if _looks_like_department_fragment(text):
            return f"{agency_short_name} {text}"
    return None


def _best_department(*candidates: str | None) -> str:
    fallback = next((candidate for candidate in reversed(candidates) if candidate), "")
    for candidate in candidates:
        if candidate and candidate != fallback:
            return candidate
    return fallback


def _looks_like_department_fragment(value: str) -> bool:
    compact = value.strip()
    if not compact or re.fullmatch(r"(?:20)?\d{2}[.\s년_-]*\d{0,2}\.?", compact):
        return False
    return bool(re.search(r"(담당관|구청장|부구청장|국장|과|팀|국|동|소|센터|실)$", compact))


def _parse_date(value: str) -> date | None:
    match = DATE_RE.search(value.strip())
    if match:
        year, month, day = (int(part) for part in match.groups())
        return date(year, month, day)
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
        if re.search(rf"\.{file_kind}(?:\b|[^\w])", lowered) or f"{file_kind}파일" in lowered:
            return file_kind
    return ""


def _looks_like_expense(value: str) -> bool:
    return any(keyword in value for keyword in EXPENSE_KEYWORDS)


def _download_looks_like_expense(*, title: str, filename: str) -> bool:
    if filename and _looks_like_expense(filename):
        return True
    if filename and not _looks_like_generic_file_label(filename):
        return False
    return _looks_like_expense(title)


def _is_download_href(href: str) -> bool:
    return any(part in href for part in DOWNLOAD_HREF_PARTS)


def _looks_like_generic_file_label(filename: str) -> bool:
    normalized = _normalize_spaces(filename).lower()
    return bool(re.fullmatch(r"(?:pdf|xls|xlsx)\s*파일\s*첨부", normalized))


def _url_with_page(url: str, page: int) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["page"] = str(page)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _response_text(response: httpx.Response) -> str:
    text = response.text
    if "�" not in text:
        return text
    decoded = response.content.decode("cp949", errors="replace")
    return decoded if decoded.count("�") < text.count("�") else text


def _normalize_spaces(value: str) -> str:
    return " ".join(value.split())
