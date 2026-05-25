from __future__ import annotations

import re
from typing import Any
from datetime import date
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx
from selectolax.parser import HTMLParser

from public_officer_pipeline.agencies import SEOUL_AGENCIES
from public_officer_pipeline.artifact import artifact_from_response, post_detail_from_artifact
from public_officer_pipeline.models import Agency, PostDetail, PostRef
from public_officer_pipeline.http_client import create_http_client
from public_officer_pipeline.source_pattern import (
    AttachmentBoardPattern,
    parse_source_pattern,
)


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
    "fileDownLoad.do",
    "/gtb_download.php",
    "/file/download/",
    "downloadBbsFile.do",
    "downloadBbsFileStr.do",
    "/WDB_common/include/download.asp",
    "/common/board/Download.do",
    "/component/file/ND_fileDownload.do",
    "/comm/getFile",
    "/portal/cmmn/file/fileDown.do",
    "/cmm/fms/FileDown.do",
    "/cwsboard/board.do?mode=download",
)
DATE_RE = re.compile(r"(20\d{2})[.-](\d{1,2})[.-](\d{1,2})")
KOREAN_DATE_RE = re.compile(r"(20\d{2})년\s*(\d{1,2})월\s*(\d{1,2})일")


class CouncilAttachmentCrawler:
    def __init__(
        self,
        agency: Agency | None = None,
        client: Any | None = None,
        source_pattern: AttachmentBoardPattern | None = None,
    ) -> None:
        self.agency = agency or next(item for item in SEOUL_AGENCIES if item.short_name == "강남구의회")
        pattern = source_pattern or parse_source_pattern(self.agency)
        if not isinstance(pattern, AttachmentBoardPattern):
            raise ValueError("CouncilAttachmentCrawler requires an attachment board pattern")
        self.list_url = pattern.listUrl
        self.follow_detail = pattern.followDetail
        self.page_param = pattern.pageParam
        self.page_unit_param = pattern.pageUnitParam or ""
        self.rows_per_page = pattern.rowsPerPage
        self.file_kinds = set(pattern.fileKinds)
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
        refs: dict[str, PostRef] = {}
        for page in range(1, limit_pages + 1):
            response = await self._client.get(
                _url_with_page(
                    self.list_url,
                    page,
                    page_param=self.page_param,
                    page_unit_param=self.page_unit_param or None,
                    rows_per_page=self.rows_per_page,
                )
            )
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
        response = await self._client.get(ref.url, headers={"Referer": self.list_url})
        response.raise_for_status()
        return post_detail_from_artifact(artifact_from_response(ref, response))

    def _parse_list(self, html: str) -> list[PostRef]:
        tree = HTMLParser(html)
        refs: list[PostRef] = []
        seen_urls: set[str] = set()
        for row in tree.css("tbody tr"):
            cells = row.css("th,td")
            if len(cells) < 4:
                continue
            title = _normalize_spaces(cells[1].text(separator=" ", strip=True))
            if not _looks_like_expense(title):
                continue
            published_at = _find_date(cells)
            for download in row.css("a[href]"):
                filename = _filename_from_download_link(download)
                href = download.attributes.get("href", "")
                file_kind = _file_kind_from_download(download, filename)
                if (
                    not href
                    or not _is_download_href(href)
                    or file_kind not in self.file_kinds
                    or not _download_looks_like_expense(title=title, filename=filename)
                ):
                    continue
                url = urljoin(self.list_url, href)
                if url in seen_urls:
                    continue
                refs.append(
                    PostRef(
                        agency_id=self.agency.id,
                        url=url,
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
                seen_urls.add(url)
        if not refs:
            refs.extend(self._parse_direct_download_table(tree))
        if not refs:
            refs.extend(self._parse_responsive_downloads(tree))
        return refs

    def _parse_direct_download_table(self, tree: HTMLParser) -> list[PostRef]:
        refs: list[PostRef] = []
        for table in tree.css("table"):
            header_row = table.css_first("thead tr") or table.css_first("tr")
            if not header_row:
                continue
            headers = [_normalize_spaces(header.text(separator=" ", strip=True)) for header in header_row.css("th")]
            compact_headers = [re.sub(r"\s+", "", header) for header in headers]
            if not {"년도", "월", "작성부서", "파일"}.issubset(set(compact_headers)):
                continue
            for row in table.css("tbody tr"):
                cells = row.css("td")
                if len(cells) < len(headers):
                    continue
                fields = {
                    compact_headers[index]: _normalize_spaces(cells[index].text(separator=" ", strip=True))
                    for index in range(min(len(headers), len(cells)))
                }
                year = fields.get("년도", "")
                month = fields.get("월") or fields.get("해당월") or ""
                department = fields.get("작성부서") or fields.get("부서") or ""
                category = fields.get("구분") or ""
                if not (year and month and department):
                    continue
                title = f"{year}년 {month.zfill(2)}월 {department} {category} 업무추진비 공개내역".strip()
                published_at = _parse_date(fields.get("작성일", "") or fields.get("등록일", ""))
                for download in row.css("a[href]"):
                    href = download.attributes.get("href", "")
                    if not href or not _is_download_href(href):
                        continue
                    filename = _filename_from_download_link(download)
                    file_kind = _file_kind_from_download(download, filename)
                    if file_kind not in self.file_kinds:
                        continue
                    filename_kind = _file_kind(filename)
                    display_filename = (
                        filename
                        if filename
                        and filename_kind == file_kind
                        and not _looks_like_uninformative_file_label(filename)
                        else f"{department} 업무추진비.{file_kind}"
                    )
                    refs.append(
                        PostRef(
                            agency_id=self.agency.id,
                            url=urljoin(self.list_url, href),
                            title=f"{title} - {display_filename}",
                            published_at=published_at,
                            department_name=_best_department(f"{self.agency.short_name} {department}", self.agency.short_name),
                            file_kind=file_kind,
                        )
                    )
        return refs

    def _parse_responsive_downloads(self, tree: HTMLParser) -> list[PostRef]:
        refs: list[PostRef] = []
        for listing in tree.css("ul.respon-td"):
            fields: dict[str, str] = {}
            for item in listing.css("li"):
                label_node = item.css_first("span")
                value_node = item.css_first("em")
                label = _normalize_spaces(label_node.text(separator=" ", strip=True)) if label_node else ""
                value = _normalize_spaces(value_node.text(separator=" ", strip=True)) if value_node else ""
                if label:
                    fields[label] = value
            year = fields.get("년도", "")
            month = fields.get("해당 월", "").zfill(2)
            department = fields.get("작성부서", "")
            category = fields.get("구분", "")
            if not (year and month and department):
                continue
            title = f"{year}년 {month}월 {department} {category} 업무추진비 공개내역".strip()
            published_at = _parse_date(fields.get("작성일", ""))
            for download in listing.css("a[href]"):
                href = download.attributes.get("href", "")
                if not href or not _is_download_href(href):
                    continue
                filename = _filename_from_download_link(download)
                file_kind = _file_kind_from_download(download, filename) or "pdf"
                if file_kind not in self.file_kinds:
                    continue
                refs.append(
                    PostRef(
                        agency_id=self.agency.id,
                        url=urljoin(self.list_url, href),
                        title=f"{title} - {department} 업무추진비.{file_kind}",
                        published_at=published_at,
                        department_name=_best_department(f"{self.agency.short_name} {department}", self.agency.short_name),
                        file_kind=file_kind,
                    )
                )
        return refs

    def _parse_detail_links(self, html: str) -> list[PostRef]:
        tree = HTMLParser(html)
        refs: list[PostRef] = []
        for row in tree.css("tbody tr"):
            cells = row.css("th,td")
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
            if not href or ("view.do" not in href.lower() and "mode=view" not in href.lower()):
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
            file_kind = _file_kind_from_download(download, filename)
            if (
                file_kind not in self.file_kinds
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
    if normalized_candidates and all(_looks_like_uninformative_file_label(item) for item in normalized_candidates):
        if download.parent:
            normalized_candidates.append(_normalize_spaces(download.parent.text(separator=" ", strip=True)).strip(" '\""))
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
    match = KOREAN_DATE_RE.search(value.strip())
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


def _file_kind_from_download(download, filename: str) -> str:
    return (
        _file_kind(filename)
        or _file_kind(download.attributes.get("href", ""))
        or _file_kind(download.attributes.get("title", ""))
    )


def _looks_like_expense(value: str) -> bool:
    return any(keyword in value for keyword in EXPENSE_KEYWORDS)


def _download_looks_like_expense(*, title: str, filename: str) -> bool:
    if filename and _looks_like_expense(filename):
        return True
    if filename and not _looks_like_generic_file_label(filename):
        return False
    return _looks_like_expense(title)


def _is_download_href(href: str) -> bool:
    if href.strip().lower().startswith("javascript:"):
        return False
    return any(part in href for part in DOWNLOAD_HREF_PARTS)


def _looks_like_generic_file_label(filename: str) -> bool:
    normalized = _normalize_spaces(filename).lower()
    return bool(re.fullmatch(r"(?:pdf|xls|xlsx)\s*파일\s*첨부", normalized))


def _looks_like_uninformative_file_label(filename: str) -> bool:
    normalized = _normalize_spaces(filename).lower()
    return normalized in {"다운로드", "첨부파일", "파일", "공개내역 파일", "바로보기"} or _looks_like_generic_file_label(
        filename
    )


def _url_with_page(
    url: str,
    page: int,
    *,
    page_param: str = "page",
    page_unit_param: str | None = None,
    rows_per_page: int | None = None,
) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query[page_param] = str(page)
    if page_unit_param and rows_per_page:
        query[page_unit_param] = str(rows_per_page)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _response_text(response: Any) -> str:
    text = response.text
    if "�" not in text:
        return text
    decoded = response.content.decode("cp949", errors="replace")
    return decoded if decoded.count("�") < text.count("�") else text


def _normalize_spaces(value: str) -> str:
    return " ".join(value.split())
