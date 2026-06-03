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
DEFAULT_USER_AGENT = (
    "PublicOfficerMapBot/0.1 "
    "(operator: wylee0806@naver.com; public-interest archive)"
)
SUPPORTED_FILE_KINDS = {"pdf", "hwp", "xls", "xlsx", "hwpx", "zip"}
EXPENSE_KEYWORDS = ("업무추진비", "업추비", "시책추진비")
DOWNLOAD_HREF_PARTS = (
    "/site/main/file/download/",
    "/bbs/FileDownLoadProc.do",
    "/board/news/download.do",
    "/boardDown.do",
    "/board/download.",
    "/download/",
    "/download.do",
    "/education/fileDownload",
    "/boardDownload.es",
    "/board_down.php",
    "/openInfoDataFileDownload.es",
    "/bbs/download.do",
    "/bbs/download?",
    "/bbs/download.php",
    "/getFile",
    "/moa/bbs/layout/basic/download.php",
    "bbsMsgFileDown.do",
    "bbsMsgFileDownCompress.do",
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
    "/attach/down/",
    "/comm/getFile",
    "/common/file/download.do",
    "/common/fileDown.do",
    "/common/file_download/",
    "/other/file_down.do",
    "/portal/cmmn/file/fileDown.do",
    "/shareEtc/download_utf.asp",
    "/board/FileDown.do",
    "/board_down.php",
    "/board/download.",
    "/boardFileDown.ac",
    "/board_download.do",
    "/bbs/download.do",
    "bbs/download.do",
    "/programs/board/download.do",
    "/common/download.php",
    "common/download.php",
    "download.php",
    "/cmm/fms/FileDown.do",
    "/cmm/fms/FileWebDown.do",
    "/egf/bp/common/front/",
    "/egf/bp/board/article/download",
    "/cmmn/file/fileDown.do",
    "/jfile/readDownloadFile.do",
    "/file/readDownloadFile.do",
    "boardDownload.es",
    "download.es",
    "/cms/download.cs",
    "/cmsfile/download.do",
    "/FileDownLoad.php",
    "/ExFileDownLoad.php",
    "/fileDownLoadDw.do",
    "/down.do",
    "/cwsboard/board.do?mode=download",
    "bbscttDownload.do",
    "act=download",
    "act=down",
    "mode=download",
)
DATE_RE = re.compile(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})")
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
        self.list_urls = [pattern.listUrl, *pattern.extraListUrls]
        self.follow_detail = pattern.followDetail
        self.page_param = pattern.pageParam
        self.page_unit_param = pattern.pageUnitParam or ""
        self.rows_per_page = pattern.rowsPerPage
        self.max_posts_cap = pattern.maxPosts
        self.js_download_path = pattern.jsDownloadPath or ""
        self.file_kinds = set(pattern.fileKinds)
        self.default_file_kind = pattern.defaultFileKind
        self.fallback_file_kind = pattern.defaultFileKind or (
            next(iter(self.file_kinds)) if len(self.file_kinds) == 1 else ""
        )
        self.http_backend = pattern.httpBackend or ""
        self.user_agent = pattern.userAgent or DEFAULT_USER_AGENT
        self.referer = pattern.referer or pattern.listUrl
        headers = {"User-Agent": self.user_agent}
        if self.referer:
            headers["Referer"] = self.referer
        client_kwargs = {
            "timeout": DEFAULT_TIMEOUT,
            "headers": headers,
            "follow_redirects": True,
        }
        if self.http_backend:
            client_kwargs["backend"] = self.http_backend
        self._client = client or create_http_client(**client_kwargs)
        self._owns_client = client is None
        self._download_referers: dict[str, str] = {}

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def list_posts(
        self,
        since: date,
        limit_pages: int = 3,
        max_posts: int | None = None,
    ) -> list[PostRef]:
        if self.max_posts_cap is not None:
            max_posts = min(max_posts, self.max_posts_cap) if max_posts is not None else self.max_posts_cap
        refs: dict[str, PostRef] = {}
        original_list_url = self.list_url
        try:
            for list_url in self.list_urls:
                self.list_url = list_url
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
                        if max_posts is not None and len(refs) >= max_posts:
                            return list(refs.values())
                    if self.follow_detail:
                        for detail in self._parse_detail_links(_response_text(response)):
                            if detail.published_at and detail.published_at < since:
                                continue
                            detail_response = await self._client.get(
                                detail.url,
                                headers={"Referer": self.list_url},
                            )
                            detail_response.raise_for_status()
                            for ref in self._parse_detail_downloads(_response_text(detail_response), detail):
                                refs[ref.url] = ref
                                if max_posts is not None and len(refs) >= max_posts:
                                    return list(refs.values())
        finally:
            self.list_url = original_list_url
        return list(refs.values())

    async def fetch_post(self, ref: PostRef) -> PostDetail:
        download_url = ref.url
        referer = self._download_referers.get(ref.url, self.list_url)
        if ref.url in self._download_referers:
            fresh_url = await self._fresh_detail_download_url(ref, referer)
            if fresh_url:
                download_url = fresh_url
                referer = self._download_referers.get(fresh_url, referer)
                ref = ref.model_copy(update={"url": fresh_url})
        response = await self._client.get(
            download_url,
            headers={"Referer": referer},
        )
        response.raise_for_status()
        return post_detail_from_artifact(artifact_from_response(ref, response))

    async def _fresh_detail_download_url(self, ref: PostRef, referer: str) -> str:
        response = await self._client.get(referer, headers={"Referer": self.list_url})
        response.raise_for_status()
        fresh_refs = self._parse_detail_downloads(
            _response_text(response),
            PostRef(
                agency_id=ref.agency_id,
                url=referer,
                title=ref.title,
                published_at=ref.published_at,
                department_name=ref.department_name,
                file_kind=ref.file_kind,
            ),
        )
        ref_identity = _download_identity(ref.url)
        for fresh_ref in fresh_refs:
            if _download_identity(fresh_ref.url) == ref_identity:
                return fresh_ref.url
        return ""

    def _parse_list(self, html: str) -> list[PostRef]:
        tree = HTMLParser(html)
        js_download_path = _egov_download_path_from_html(html) or self.js_download_path
        refs: list[PostRef] = []
        seen_urls: set[str] = set()
        for row in tree.css("tbody tr"):
            cells = row.css("th,td")
            if len(cells) < 2:
                continue
            title = _clean_title(_normalize_spaces(cells[1].text(separator=" ", strip=True)))
            if not _looks_like_expense(title):
                continue
            published_at = _find_date(cells)
            for download in row.css("a[href]"):
                filename = _filename_from_download_link(download)
                href = _download_href_from_anchor(download, js_download_path)
                file_kind = _file_kind_from_download(download, filename) or self.fallback_file_kind
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
            refs.extend(self._parse_header_mapped_download_table(tree))
        if not refs:
            refs.extend(self._parse_direct_download_table(tree))
        if not refs:
            refs.extend(self._parse_data_column_download_table(tree))
        if not refs:
            refs.extend(self._parse_responsive_downloads(tree))
        if not refs:
            refs.extend(self._parse_file_list_items(tree))
        if not refs:
            refs.extend(self._parse_current_detail_downloads(tree))
        if not refs:
            refs.extend(self._parse_daily_html_detail_refs(tree))
        return _sort_download_refs(refs)

    def _parse_header_mapped_download_table(self, tree: HTMLParser) -> list[PostRef]:
        refs: list[PostRef] = []
        seen_urls: set[str] = set()
        for table in tree.css("table"):
            header_row = table.css_first("thead tr") or table.css_first("tr")
            if not header_row:
                continue
            headers = [
                re.sub(r"\s+", "", _normalize_spaces(header.text(separator=" ", strip=True)))
                for header in header_row.css("th")
            ]
            title_index = _column_index(headers, "제목", "업무명", "공개일자")
            file_index = _column_index(headers, "파일", "첨부")
            if title_index is None or file_index is None:
                continue
            date_index = _column_index(headers, "작성일", "등록일", "일자", "날짜")
            department_index = _column_index(headers, "담당부서", "작성부서", "부서")
            for row in table.css("tbody tr"):
                cells = row.css("th,td")
                if len(cells) <= max(title_index, file_index):
                    continue
                title = _clean_title(_normalize_spaces(cells[title_index].text(separator=" ", strip=True)))
                if not _looks_like_expense(title):
                    continue
                published_at = (
                    _parse_date(cells[date_index].text(separator=" ", strip=True))
                    if date_index is not None and date_index < len(cells)
                    else _find_date(cells)
                )
                department = ""
                if department_index is not None and department_index < len(cells):
                    department = _normalize_spaces(cells[department_index].text(separator=" ", strip=True))
                download_scope = cells[file_index]
                row_links = (
                    row.css("a[href]")
                    if all(_looks_like_uninformative_file_label(_filename_from_download_link(item)) for item in download_scope.css("a[href]"))
                    else download_scope.css("a[href]")
                )
                for download in row_links:
                    filename = _filename_from_download_link(download)
                    href = _download_href_from_anchor(download, self.js_download_path)
                    file_kind = _file_kind_from_download(download, filename) or self.fallback_file_kind
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
                    seen_urls.add(url)
                    refs.append(
                        PostRef(
                            agency_id=self.agency.id,
                            url=url,
                            title=f"{title} - {filename}",
                            published_at=published_at,
                            department_name=_best_department(
                                _department_from_filename(filename, self.agency.short_name),
                                _department_from_filename(title, self.agency.short_name),
                                f"{self.agency.short_name} {department}"
                                if _looks_like_department_fragment(department)
                                else None,
                                self.agency.short_name,
                            ),
                            file_kind=file_kind,
                        )
                    )
        return _sort_download_refs(refs)

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
                    href = _download_href_from_anchor(download, self.js_download_path)
                    if not href or not _is_download_href(href):
                        continue
                    filename = _filename_from_download_link(download)
                    file_kind = (
                        _file_kind_from_download(download, filename)
                        or _file_kind(href)
                        or self.fallback_file_kind
                    )
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
        return _sort_download_refs(refs)

    def _parse_data_column_download_table(self, tree: HTMLParser) -> list[PostRef]:
        refs: list[PostRef] = []
        seen_urls: set[str] = set()
        for row in tree.css("tbody tr"):
            cells = row.css("td[data-column]")
            if len(cells) < 4:
                continue
            values_by_column: dict[str, list[str]] = {}
            cells_by_column: dict[str, list[Any]] = {}
            for cell in cells:
                column = _normalize_spaces(cell.attributes.get("data-column", ""))
                if not column:
                    continue
                values_by_column.setdefault(column, []).append(
                    _normalize_spaces(cell.text(separator=" ", strip=True))
                )
                cells_by_column.setdefault(column, []).append(cell)
            year_values = values_by_column.get("연도", [])
            year = next((value for value in year_values if re.fullmatch(r"20\d{2}", value)), "")
            month = next(
                (value for value in year_values if value != year and re.fullmatch(r"\d{1,2}", value)),
                "",
            )
            department = next(
                (
                    value
                    for value in values_by_column.get("제목", []) + values_by_column.get("구분", [])
                    if value
                ),
                "",
            )
            if not (year and month and department):
                continue
            title = f"{year}년 {month.zfill(2)}월 {department} 업무추진비 공개내역"
            published_at = _parse_date(" ".join(values_by_column.get("작성일", [])))
            download_cells = cells_by_column.get("첨부파일", []) + cells_by_column.get("사용내역", [])
            download_links = []
            for cell in download_cells:
                download_links.extend(cell.css("a[href]"))
            for download in download_links:
                href = _download_href_from_anchor(download, self.js_download_path)
                if not href or not _is_download_href(href):
                    continue
                filename = _filename_from_download_link(download)
                file_kind = (
                    _file_kind_from_download(download, filename)
                    or _file_kind(href)
                    or self.fallback_file_kind
                )
                if file_kind not in self.file_kinds:
                    continue
                display_filename = (
                    filename
                    if filename
                    and _file_kind(filename) == file_kind
                    and not _looks_like_uninformative_file_label(filename)
                    else f"{department} 업무추진비.{file_kind}"
                )
                url = urljoin(self.list_url, href)
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                refs.append(
                    PostRef(
                        agency_id=self.agency.id,
                        url=url,
                        title=f"{title} - {display_filename}",
                        published_at=published_at,
                        department_name=_best_department(
                            f"{self.agency.short_name} {department}",
                            self.agency.short_name,
                        ),
                        file_kind=file_kind,
                    )
                )
        return _sort_download_refs(refs)

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
        return _sort_download_refs(refs)

    def _parse_file_list_items(self, tree: HTMLParser) -> list[PostRef]:
        refs: list[PostRef] = []
        seen_urls: set[str] = set()
        items = tree.css(".board_list ul.generalList > li") + tree.css("ul.board_list > li")
        if not items:
            items = tree.css("li")
        for item in items:
            title_parent = item.css_first("p.title")
            if title_parent is None:
                continue
            title_node = title_parent.css_first("a[href]")
            if not title_node:
                continue
            title = _clean_title(_normalize_spaces(title_node.text(separator=" ", strip=True)))
            if not _looks_like_expense(title):
                continue
            published_at = _parse_date(
                _normalize_spaces(
                    (item.css_first(".writer_info .center") or item.css_first("li.center") or item).text(
                        separator=" ",
                        strip=True,
                    )
                )
            )
            writer = _normalize_spaces(
                (item.css_first(".writer_info .writer") or item.css_first("li.writer") or item).text(
                    separator=" ",
                    strip=True,
                )
            )
            for download in item.css(".file a[href], li.file a[href], a[href]"):
                href = download.attributes.get("href", "")
                if not href or not _is_download_href(href):
                    continue
                filename = _filename_from_download_link(download)
                file_kind = _file_kind_from_download(download, filename) or self.fallback_file_kind
                if file_kind not in self.file_kinds:
                    continue
                url = urljoin(self.list_url, href)
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                refs.append(
                    PostRef(
                        agency_id=self.agency.id,
                        url=url,
                        title=f"{title} - {filename or file_kind}",
                        published_at=published_at,
                        department_name=_best_department(
                            _department_from_filename(filename, self.agency.short_name),
                            _department_from_filename(title, self.agency.short_name),
                            f"{self.agency.short_name} {writer}" if _looks_like_department_fragment(writer) else None,
                            self.agency.short_name,
                        ),
                        file_kind=file_kind,
                    )
                )
        return _sort_download_refs(refs)

    def _parse_current_detail_downloads(self, tree: HTMLParser) -> list[PostRef]:
        title_node = (
            tree.css_first(".board-post-title-text")
            or tree.css_first(".board-post-title")
            or tree.css_first("h1")
        )
        title = (
            _clean_title(_normalize_spaces(title_node.text(separator=" ", strip=True)))
            if title_node
            else ""
        )
        if not _looks_like_expense(title):
            return []

        published_at = None
        for item in tree.css(".board-post-meta-text, .skinTb-date, time"):
            published_at = _parse_date(item.text(separator=" ", strip=True))
            if published_at:
                break

        refs: list[PostRef] = []
        seen_urls: set[str] = set()
        for download in tree.css("a[href]"):
            href = _download_href_from_anchor(download, self.js_download_path)
            if not href or not _is_download_href(href):
                continue
            filename = _filename_from_download_link(download)
            file_kind = _file_kind(filename) or _file_kind(href) or _file_kind_from_download(download, filename)
            if (
                file_kind not in self.file_kinds
                or not _download_looks_like_expense(title=title, filename=filename)
            ):
                continue
            url = urljoin(self.list_url, href)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            refs.append(
                PostRef(
                    agency_id=self.agency.id,
                    url=url,
                    title=f"{title} - {filename}",
                    published_at=published_at,
                    department_name=_best_department(
                        _department_from_filename(filename or title, self.agency.short_name),
                        _department_from_filename(title, self.agency.short_name),
                        self.agency.short_name,
                    ),
                    file_kind=file_kind,
                )
            )
        return refs

    def _parse_daily_html_detail_refs(self, tree: HTMLParser) -> list[PostRef]:
        if "html" not in self.file_kinds:
            return []

        refs: list[PostRef] = []
        seen_urls: set[str] = set()
        for row in tree.css("tbody tr"):
            cells = row.css("th,td")
            if len(cells) < 3:
                continue
            trigger = " ".join(
                value
                for anchor in row.css("a[href]")
                for value in (
                    anchor.attributes.get("onclick", ""),
                    anchor.attributes.get("href", ""),
                )
            )
            detail_date = re.search(r"\bf_detail\(['\"](?P<date>20\d{2}-\d{1,2}-\d{1,2})['\"]\)", trigger)
            if not detail_date:
                continue
            title = _clean_title(
                _normalize_spaces(
                    (row.css_first("a[href]") or cells[-2]).text(separator=" ", strip=True)
                )
            )
            if not _looks_like_expense(title):
                continue
            published_at = _parse_date(detail_date.group("date")) or _find_date(cells)
            parts = urlsplit(self.list_url)
            query = dict(parse_qsl(parts.query, keep_blank_values=True))
            query["useDe"] = detail_date.group("date")
            url = urljoin(
                self.list_url,
                urlunsplit(("", "", parts.path, urlencode(query), parts.fragment)),
            )
            if url in seen_urls:
                continue
            seen_urls.add(url)
            refs.append(
                PostRef(
                    agency_id=self.agency.id,
                    url=url,
                    title=title,
                    published_at=published_at,
                    department_name=self.agency.short_name,
                    file_kind="html",
                )
            )
        return _sort_download_refs(refs)

    def _parse_detail_links(self, html: str) -> list[PostRef]:
        tree = HTMLParser(html)
        refs: list[PostRef] = []
        for row in tree.css("tbody tr"):
            cells = row.css("th,td")
            if len(cells) < 4:
                continue
            title_cell = _detail_title_cell(cells)
            if title_cell is None:
                continue
            title = _clean_title(_normalize_spaces(title_cell.text(separator=" ", strip=True)))
            if not _looks_like_expense(title):
                continue
            anchor = title_cell.css_first("a[href]")
            row_onclick = row.attributes.get("onclick", "")
            if not anchor and not any(
                marker in row_onclick
                for marker in ("fnActDetail", "boardViewRenewal", "BoardDetailView")
            ):
                continue
            script_title = re.search(r"wdigm_title\('(?P<title>[^']+)'\)", title)
            if script_title:
                title = script_title.group("title")
            href = anchor.attributes.get("href", "") if anchor else ""
            onclick = anchor.attributes.get("onclick", "") if anchor else ""
            trigger = f"{onclick} {href}"
            row_trigger = f"{trigger} {row_onclick}"
            act_detail = re.search(r"fnActDetail\([\"'](?P<view_no>[^\"']+)[\"']\)", f"{trigger} {row_onclick}")
            if act_detail:
                parts = urlsplit(self.list_url)
                detail_path = re.sub(r"reportList\.do$", "reportView.do", parts.path)
                href = f"{detail_path}?viewNo={act_detail.group('view_no')}"
            board_view = re.search(
                r"boardViewRenewal\(\s*['\"][^'\"]+['\"]\s*,\s*['\"][^'\"]*['\"]\s*,"
                r"\s*['\"]Y['\"]\s*,\s*['\"](?P<bc_idx>[^'\"]+)['\"]\s*,"
                r"\s*['\"](?P<idx>[^'\"]+)['\"]\s*,\s*['\"](?P<mid>[^'\"]+)['\"]",
                row_trigger,
            )
            if board_view:
                parts = urlsplit(self.list_url)
                detail_path = re.sub(r"list\.do$", "view.do", parts.path)
                href = (
                    f"{detail_path}?mid={board_view.group('mid')}"
                    f"&bcIdx={board_view.group('bc_idx')}"
                    f"&idx={board_view.group('idx')}"
                )
            board_view = re.search(
                r"\bboardView\(\s*['\"](?P<site>[^'\"]+)['\"]\s*,\s*['\"][^'\"]+['\"]\s*,"
                r"\s*['\"][^'\"]*['\"]\s*,\s*['\"][^'\"]*['\"]\s*,"
                r"\s*['\"](?P<b_idx>[^'\"]+)['\"]\s*,\s*['\"](?P<pt_idx>[^'\"]+)['\"]\s*,"
                r"\s*['\"](?P<mid>[^'\"]+)['\"]",
                row_trigger,
            )
            if board_view:
                href = (
                    f"/{board_view.group('site')}/bbs/view.do"
                    f"?mId={board_view.group('mid')}"
                    f"&bIdx={board_view.group('b_idx')}"
                    f"&ptIdx={board_view.group('pt_idx')}"
                )
            hwasun_board_detail = re.search(
                r"BoardDetailView\(['\"](?P<bbs_sn>[^'\"]+)['\"]\)",
                row_trigger,
            )
            if hwasun_board_detail:
                parts = urlsplit(self.list_url)
                query = dict(parse_qsl(parts.query, keep_blank_values=True))
                query["bbsSn"] = hwasun_board_detail.group("bbs_sn")
                href = urlunsplit(("", "", parts.path, urlencode(query), ""))
            bbs_view = re.search(r"doBbsFView\('(?P<cb_idx>[^']+)'\s*,\s*'(?P<bc_idx>[^']+)'", onclick)
            if bbs_view:
                href = (
                    "/site/yangcheon/ex/bbs/View.do"
                    f"?cbIdx={bbs_view.group('cb_idx')}&bcIdx={bbs_view.group('bc_idx')}"
                )
            bbs_view_four_args = re.search(
                r"doBbsFView\('(?P<cb_idx>[^']+)'\s*,\s*'(?P<bc_idx>[^']+)'\s*,"
                r"\s*'(?P<menu>[^']*)'\s*,\s*'(?P<ntt>[^']+)'",
                onclick,
            )
            if bbs_view_four_args:
                parts = urlsplit(self.list_url)
                href = (
                    f"{parts.path.replace('List.do', 'View.do')}"
                    f"?cbIdx={bbs_view_four_args.group('cb_idx')}"
                    f"&bcIdx={bbs_view_four_args.group('bc_idx')}"
                    f"&nttNo={bbs_view_four_args.group('ntt')}"
                )
            data_view_jsp = re.search(r"dataView\.jsp\?(?P<query>[^'\" ]+)", trigger)
            if data_view_jsp:
                parts = urlsplit(self.list_url)
                href = f"{parts.path.rsplit('/', 1)[0]}/dataView.jsp?{data_view_jsp.group('query')}"
            fn_view = re.search(r"fnView\(\s*['\"]?(?P<id>[^,'\")]+)['\"]?", trigger)
            if fn_view and (not href or _is_placeholder_href(href) or href.lower().startswith("javascript")):
                parts = urlsplit(self.list_url)
                query = dict(parse_qsl(parts.query, keep_blank_values=True))
                query["nttId"] = fn_view.group("id")
                detail_path = re.sub(r"(?:list|List)\.do$", "view.do", parts.path)
                href = urlunsplit(("", "", detail_path, urlencode(query), ""))
            fn_select_doc = re.search(r"fn_selectDoc\(\s*['\"]?(?P<id>[^,'\")]+)['\"]?", trigger)
            if fn_select_doc:
                parts = urlsplit(self.list_url)
                detail_path = re.sub(r"selectDocList\.do$", "selectDocView.do", parts.path)
                query = dict(parse_qsl(parts.query, keep_blank_values=True))
                query["docSeq"] = fn_select_doc.group("id")
                href = urlunsplit(("", "", detail_path, urlencode(query), ""))
            bd_board_view = re.search(
                r"jsView\(\s*['\"](?P<bbs_cd>[^'\"]+)['\"]\s*,\s*['\"](?P<seq>[^'\"]+)['\"]",
                trigger,
            )
            if bd_board_view:
                parts = urlsplit(self.list_url)
                detail_path = re.sub(r"BD_board\.list\.do$", "BD_board.view.do", parts.path)
                href = (
                    f"{detail_path}?bbsCd={bd_board_view.group('bbs_cd')}"
                    f"&seq={bd_board_view.group('seq')}"
                )
            portal_bbs_view = re.search(
                r"goTo\.view\('list'\s*,\s*'(?P<b_idx>[^']+)'\s*,\s*'(?P<pt_idx>[^']+)'\s*,\s*'(?P<m_id>[^']+)'",
                onclick,
            )
            if portal_bbs_view:
                href = (
                    "/portal/bbs/view.do"
                    f"?bIdx={portal_bbs_view.group('b_idx')}"
                    f"&ptIdx={portal_bbs_view.group('pt_idx')}"
                    f"&mId={portal_bbs_view.group('m_id')}"
                )
            page_list_bbs_view = re.search(r"fnGoDetail\(\s*(?P<bbs_seq>\d+)\s*\)", onclick)
            if page_list_bbs_view:
                query = dict(parse_qsl(urlsplit(self.list_url).query, keep_blank_values=True))
                bbs_code = query.get("bbs_code", "")
                href = (
                    "/www/common/bbs/selectBbsDetail.do"
                    f"?bbs_seq={page_list_bbs_view.group('bbs_seq')}"
                    f"{f'&bbs_code={bbs_code}' if bbs_code else ''}"
                )
            data_view = re.search(r"dataView\('(?P<idx>[^']+)'\)", trigger)
            if data_view:
                list_parts = urlsplit(self.list_url)
                detail_path = re.sub(r"bbsList\.do$", "bbsView.do", list_parts.path)
                href = f"{detail_path}?idx={data_view.group('idx')}"
            info_bbs_view = re.search(r"goViewPage\('(?P<bbs_sn>[^']+)'\)", trigger)
            if info_bbs_view:
                parts = urlsplit(self.list_url)
                query = dict(parse_qsl(parts.query, keep_blank_values=True))
                query["bbsSn"] = info_bbs_view.group("bbs_sn")
                detail_path = re.sub(r"List\.php$", "View.php", parts.path)
                href = urlunsplit(("", "", detail_path, urlencode(query), ""))
            article_seq_view = re.search(r"goPage2?\(\s*['\"]?(?P<article_seq>\d+)['\"]?\s*\)", row_trigger)
            if article_seq_view:
                parts = urlsplit(self.list_url)
                query = dict(parse_qsl(parts.query, keep_blank_values=True))
                query["articleSeq"] = article_seq_view.group("article_seq")
                href = urlunsplit(("", "", parts.path, urlencode(query), parts.fragment))
            data_opt = anchor.attributes.get("data-opt", "") if anchor else ""
            if data_opt and "." in data_opt:
                checksum, post_id = data_opt.split(".", 1)
                parts = urlsplit(self.list_url)
                query = dict(parse_qsl(parts.query, keep_blank_values=True))
                query.setdefault("page", "1")
                query.update({"sp": "2", "wr_id": post_id, "chk": checksum})
                href = urlunsplit(("", "", parts.path, urlencode(query), ""))
            go_bbs_view = re.search(r"goBbsViewPage\(['\"](?P<bbs_sn>[^'\"]+)['\"]\)", row_trigger)
            if go_bbs_view:
                parts = urlsplit(self.list_url)
                query = _hidden_form_query(tree, "bbsViewPageFrm")
                query["schBbsSn"] = go_bbs_view.group("bbs_sn")
                detail_path = re.sub(r"List\.do$", "View.do", parts.path)
                href = urlunsplit(("", "", detail_path, urlencode(query), ""))
            inline_post_idx = anchor.attributes.get("data-req-get-p-idx", "") if anchor else ""
            if inline_post_idx:
                parts = urlsplit(self.list_url)
                query = dict(parse_qsl(parts.query, keep_blank_values=True))
                query["idx"] = inline_post_idx
                detail_path = re.sub(r"list\.do$", "view.do", parts.path)
                href = urlunsplit(("", "", detail_path, urlencode(query), ""))
            inline_post_href = _inline_post_detail_href(anchor)
            if inline_post_href:
                href = inline_post_href
            gunwi_page_href = _gunwi_page_detail_href(href)
            if gunwi_page_href:
                href = gunwi_page_href
            if not href or _is_placeholder_href(href):
                continue
            href = _strip_path_jsessionid(href)
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
            title = _clean_title(_normalize_spaces(anchor.text(separator=" ", strip=True)))
            if not _looks_like_expense(title):
                continue
            href = anchor.attributes.get("href", "")
            if not href or not _is_detail_href_for_list(href, self.list_url):
                continue
            href = _strip_path_jsessionid(href)
            url = urljoin(self.list_url, href)
            if url in seen:
                continue
            row = anchor
            while row is not None and getattr(row, "tag", "") != "tr":
                row = row.parent
            published_at = _parse_date(anchor.parent.text(separator=" ", strip=True)) if anchor.parent else None
            if row is not None:
                published_at = _find_date(row.css("th,td")) or published_at
            refs.append(
                PostRef(
                    agency_id=self.agency.id,
                    url=url,
                    title=title,
                    published_at=published_at,
                    department_name=_department_from_filename(title, self.agency.short_name),
                    file_kind="html",
                )
            )
            seen.add(url)
        return refs

    def _parse_detail_downloads(self, html: str, detail: PostRef) -> list[PostRef]:
        tree = HTMLParser(html)
        js_download_path = _egov_download_path_from_html(html) or self.js_download_path
        refs: list[PostRef] = []
        seen_urls: set[str] = set()
        for download in [*tree.css("a[href]"), *tree.css("[onclick]")]:
            href = _download_href_from_anchor(download, js_download_path)
            if not href or not _is_download_href(href):
                continue
            filename = _filename_from_download_link(download)
            file_kind = (
                _file_kind(filename)
                or _file_kind(href)
                or _file_kind_from_download(download, filename)
                or self.fallback_file_kind
            )
            if (
                file_kind not in self.file_kinds
                or not _download_looks_like_expense(title=detail.title, filename=filename)
            ):
                continue
            url = urljoin(detail.url, href)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            self._download_referers[url] = detail.url
            refs.append(
                PostRef(
                    agency_id=self.agency.id,
                    url=url,
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
        return _sort_download_refs(refs)


class GangnamCouncilCrawler(CouncilAttachmentCrawler):
    pass


def _download_href_from_anchor(download, js_download_path: str = "") -> str:
    href = download.attributes.get("href", "") or ""
    onclick = download.attributes.get("onclick", "") or ""
    trigger = f"{onclick} {href}"
    window_open = re.search(
        r"window\.open\(\s*['\"](?P<url>[^'\"]+)['\"]",
        trigger,
    )
    if window_open and _is_window_open_download_candidate(window_open.group("url")):
        return window_open.group("url")
    js_download = re.search(
        r"yhLib\.file\.download\('(?P<attach_id>[^']+)'\s*,\s*'(?P<file_sn>[^']+)'",
        onclick,
    )
    if js_download:
        return (
            "/common/file/download.do"
            f"?atchFileId={js_download.group('attach_id')}&fileSn={js_download.group('file_sn')}"
        )
    file_down_load = re.search(r"fnFileDownLoad\('(?P<file_id>[^']+)'\)", onclick)
    if file_down_load:
        return f"/common/file/FileDown.do?file_id={file_down_load.group('file_id')}"
    egov_down_file = re.search(
        r"fn_egov_downFile\('(?P<atch_file_id>[^']+)'\s*,\s*'(?P<file_sn>[^']+)'\)",
        trigger,
    )
    if egov_down_file:
        download_path = js_download_path or "/cmm/fms/FileDown.do"
        return (
            f"{download_path}?atchFileId={egov_down_file.group('atch_file_id')}"
            f"&fileSn={egov_down_file.group('file_sn')}"
        )
    act_download = re.search(
        r"fn(?:Act|App|Src)Download\([\"'](?P<file_id>[^\"']+)[\"'](?:\s*,\s*[\"'](?P<file_type>[^\"']+)[\"'])?\)",
        trigger,
    )
    if act_download:
        query = {"fileID": act_download.group("file_id")}
        if act_download.group("file_type"):
            query["fileType"] = act_download.group("file_type")
        return "/cmmn/FileDown.do?" + urlencode(query)
    seongnam_file_download = re.search(
        r"fileDownload\('(?P<file_path>[^']+)'\s*,\s*'(?P<save_file_name>[^']+)'\s*,\s*'(?P<original_file_name>[^']+)'\)",
        trigger,
    )
    if seongnam_file_download:
        return "/fileDownload.do?" + urlencode(
            {
                "filePath": seongnam_file_download.group("file_path"),
                "saveFileNm": seongnam_file_download.group("save_file_name"),
                "oFileNm": seongnam_file_download.group("original_file_name"),
            }
        )
    path_file_download = re.search(
        r"fileDownLoad\('(?P<file_path>[^']+)'\s*,\s*'(?P<file_name>[^']+)'\)",
        trigger,
    )
    if path_file_download and (
        "/" in path_file_download.group("file_path")
        or _file_kind(path_file_download.group("file_path"))
        or _file_kind(path_file_download.group("file_name"))
    ):
        return "/cmm/Download.do?" + urlencode(
            {
                "filePath": path_file_download.group("file_path"),
                "fileName": path_file_download.group("file_name"),
            }
        )
    php_file_down_load = re.search(
        r"fileDownLoad\('(?P<file_id>[^']+)'\s*,\s*'(?P<file_cd>[^']+)'\)",
        trigger,
    )
    if php_file_down_load and js_download_path:
        return (
            f"{js_download_path}"
            f"?flSn={php_file_down_load.group('file_id')}"
            f"&flCd={php_file_down_load.group('file_cd')}"
        )
    bbs_file_download = re.search(
        r"goBbsFileDownload\(['\"](?P<file_id>[^'\"]+)['\"]\s*,\s*['\"](?P<bbs_cd>[^'\"]+)['\"]\)",
        trigger,
    )
    if bbs_file_download:
        return "/bbs/FileDownLoadProc.do?" + urlencode(
            {
                "schFlSn": bbs_file_download.group("file_id"),
                "bbsCd": bbs_file_download.group("bbs_cd"),
            }
        )
    open_download_files = re.search(r"openDownloadFiles\((?P<file_uid>\d+)\)", trigger)
    if open_download_files:
        return "/programs/board/download.do?" + urlencode(
            {"parm_file_uid": open_download_files.group("file_uid")}
        )
    zip_download = re.search(r"fn_zipDownload\(['\"](?P<attach_id>[^'\"]+)['\"]\)", trigger)
    if zip_download:
        return "/cmm/fms/zipDownload.do?" + urlencode(
            {
                "atchFileIdStr": zip_download.group("attach_id"),
                "zipFileName": "zipDownload.zip",
            }
        )
    return href


def _strip_path_jsessionid(href: str) -> str:
    parts = urlsplit(href)
    path = re.sub(r";jsessionid=[^/?#]+", "", parts.path, flags=re.IGNORECASE)
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


def _hidden_form_query(tree: HTMLParser, form_id: str) -> dict[str, str]:
    form = tree.css_first(f"form#{form_id}") or tree.css_first(f"form[name='{form_id}']")
    if not form:
        return {}
    query: dict[str, str] = {}
    for item in form.css("input[name]"):
        name = item.attributes.get("name", "")
        if name:
            query[name] = item.attributes.get("value", "")
    return query


def _egov_download_path_from_html(html: str) -> str:
    match = re.search(
        r"window\.open\([\"'](?P<path>[^\"']*FileDown\.do(?:;jsessionid=[^?\"']+)?)\?atchFileId=",
        html,
    )
    return match.group("path") if match else ""


def _inline_post_detail_href(anchor) -> str:
    if not anchor:
        return ""
    action = anchor.attributes.get("data-req-action", "")
    bid = anchor.attributes.get("data-req-p-bid", "")
    if not action or not bid:
        return ""
    parts = urlsplit(action)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["bid"] = bid
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _gunwi_page_detail_href(href: str) -> str:
    parts = urlsplit(href)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if parts.path.endswith("page.do") or not parts.path:
        if query.get("cmd") == "2" and query.get("bod_uid") and query.get("mnu_uid"):
            query["cmd"] = "258"
            return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    return ""


def _detail_title_cell(cells) -> Any | None:
    for cell in cells:
        title = _clean_title(_normalize_spaces(cell.text(separator=" ", strip=True)))
        if _looks_like_expense(title) and cell.css_first("a[href]"):
            return cell
    if len(cells) > 1:
        return cells[1]
    return None


def _filename_from_download_link(download) -> str:
    trigger = f"{download.attributes.get('onclick', '')} {download.attributes.get('href', '')}"
    if "fn_zipDownload" in trigger:
        return "zipDownload.zip"
    candidates = [
        download.text(separator=" ", strip=True) or "",
        download.attributes.get("title") or "",
    ]
    image = download.css_first("img")
    if image:
        candidates.append(image.attributes.get("alt") or "")
    normalized_candidates = []
    for candidate in candidates:
        normalized = _normalize_spaces(candidate)
        if not normalized:
            continue
        if "파일 내려받기" in normalized:
            normalized = normalized.replace("파일 내려받기", "")
        normalized_candidates.append(normalized.strip(" '\""))
    if normalized_candidates and all(_looks_like_uninformative_file_label(item) for item in normalized_candidates):
        parent = download.parent
        for _ in range(3):
            if not parent:
                break
            parent_text = _normalize_spaces(parent.text(separator=" ", strip=True)).strip(" '\"")
            if parent_text and len(parent_text) <= 500:
                normalized_candidates.append(parent_text)
            parent = parent.parent
    for candidate in normalized_candidates:
        if _file_kind(candidate) or _looks_like_expense(candidate):
            return candidate
    if normalized_candidates:
        return normalized_candidates[0]
    return ""


def _department_from_filename(filename: str, agency_short_name: str = "강남구의회") -> str:
    if "사무국" in filename:
        return f"{agency_short_name} 사무국"
    if "부지사" in filename:
        return f"{agency_short_name} 부지사"
    if "도지사" in filename:
        return f"{agency_short_name} 도지사"
    if "부시장" in filename:
        return f"{agency_short_name} 부시장"
    if re.search(r"(?<!부)시장", filename):
        return f"{agency_short_name} 시장"
    if "부군수" in filename:
        return f"{agency_short_name} 부군수"
    if re.search(r"(?<!부)군수", filename):
        return f"{agency_short_name} 군수"
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
        r"\d{1,2}월\s+(?P<department>[가-힣0-9]+(?:담당관|전문위원|구청장|부구청장|국장|과|팀|국|동|소|센터|실))",
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


def _column_index(headers: list[str], *candidates: str) -> int | None:
    for index, header in enumerate(headers):
        if any(candidate in header for candidate in candidates):
            return index
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
    return bool(re.search(r"(담당관|전문위원|구청장|부구청장|국장|과|팀|국|동|소|센터|실)$", compact))


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


def _file_kind(filename: str | None) -> str:
    lowered = (filename or "").lower()
    normalized = _normalize_spaces(filename or "").lower()
    if "excel" in normalized or "엑셀" in normalized:
        return "xlsx"
    if "hwpx" in normalized:
        return "hwpx"
    if "한글" in normalized or re.search(r"\bhwp\b|\.hwp(?:\b|[^\w])", normalized):
        return "hwp"
    for file_kind in SUPPORTED_FILE_KINDS:
        if (
            re.search(rf"\.{file_kind}(?:\b|[^\w])", lowered)
            or f"{file_kind}파일" in lowered
            or re.search(rf"\b{file_kind}\s*파일\b", lowered)
            or re.search(rf"\b{file_kind}\s*첨부파일\b", lowered)
        ):
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
    if filename.lower().endswith(".zip"):
        return _looks_like_expense(title)
    if filename and _looks_like_expense(filename):
        return True
    if filename and not _looks_like_uninformative_file_label(filename):
        return False
    return _looks_like_expense(title)


def _is_download_href(href: str) -> bool:
    if _is_placeholder_href(href):
        return False
    lowered = href.lower()
    if (
        "downloadview.do" in lowered
        or "pre_viewer.php" in lowered
        or "synap.jsp" in lowered
        or "synap/" in lowered
        or "synep.jsp" in lowered
        or "convert.jsp" in lowered
    ):
        return False
    if "mode=d" in lowered and "file_id=" in lowered:
        return True
    return any(part.lower() in lowered for part in DOWNLOAD_HREF_PARTS) or re.search(
        r"\.(?:pdf|hwp|xls|xlsx|hwpx|zip)(?:$|[?#&])",
        lowered,
    ) is not None


def _is_window_open_download_candidate(href: str) -> bool:
    if not href:
        return False
    lowered = href.lower()
    if any(
        marker in lowered
        for marker in (
            "downloadview.do",
            "pre_viewer.php",
            "synap",
            "convert.jsp",
            "viewer",
        )
    ):
        return False
    return _is_download_href(href) or "file_download" in lowered or _file_kind(href) != ""


def _is_detail_href(href: str) -> bool:
    lowered = href.strip().lower()
    if _is_placeholder_href(href):
        return False
    return (
        "view.do" in lowered
        or "selectboarddetail.do" in lowered
        or "dataview.jsp" in lowered
        or "read.do" in lowered
        or "act=view" in lowered
        or "mode=view" in lowered
        or "mode=v" in lowered
        or "m_mode=view" in lowered
        or "amode=view" in lowered
        or "type=view" in lowered
        or "act=view" in lowered
        or "articleseq=" in lowered
        or "cmd=2" in lowered
        or "bd_selectbbs.do" in lowered
        or ("pg=vv" in lowered and "fidx=" in lowered)
        or re.search(r"/read/\d+(?:$|[?#/])", lowered) is not None
        or re.search(r"(?:^|/)view(?:\?|$)", lowered) is not None
    )


def _is_detail_href_for_list(href: str, list_url: str) -> bool:
    if _is_detail_href(href):
        return True
    if _is_placeholder_href(href):
        return False
    list_parts = urlsplit(list_url)
    href_parts = urlsplit(urljoin(list_url, href))
    if list_parts.netloc and href_parts.netloc != list_parts.netloc:
        return False
    list_path = list_parts.path.rstrip("/")
    href_path = href_parts.path.rstrip("/")
    if not list_path or not href_path.startswith(f"{list_path}/"):
        return False
    return re.fullmatch(r"/\d+", href_path.removeprefix(list_path)) is not None


def _is_placeholder_href(href: str) -> bool:
    lowered = href.strip().lower()
    return not lowered or lowered == "#" or lowered.startswith("javascript:") or "void(0)" in lowered


def _looks_like_generic_file_label(filename: str) -> bool:
    normalized = _normalize_spaces(filename).lower()
    return bool(
        re.fullmatch(
            r"(?:pdf|xls|xlsx|hwpx)\s*(?:(?:첨부)?파일\s*)?(?:첨부|다운로드|미리보기)",
            normalized,
        )
    )


def _looks_like_uninformative_file_label(filename: str) -> bool:
    normalized = _normalize_spaces(filename).lower()
    return normalized in {
        "다운로드",
        "내려받기",
        "첨부파일",
        "첨부파일 다운로드",
        "파일",
        "파일 다운로드",
        "파일이 여러개 있음",
        "공개내역 파일",
        "바로보기",
    } or _looks_like_generic_file_label(filename)


def _file_kind_priority(file_kind: str) -> int:
    return {
        "xlsx": 0,
        "xls": 1,
        "html": 2,
        "hwpx": 3,
        "zip": 4,
        "pdf": 5,
        "hwp": 6,
    }.get(file_kind, 9)


def _sort_download_refs(refs: list[PostRef]) -> list[PostRef]:
    return sorted(refs, key=lambda ref: _file_kind_priority(ref.file_kind))


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


def _download_identity(url: str) -> str:
    parts = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in {"pkey", "token", "key"}
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def _response_text(response: Any) -> str:
    text = response.text
    if "�" not in text:
        return text
    decoded = response.content.decode("cp949", errors="replace")
    return decoded if decoded.count("�") < text.count("�") else text


def _clean_title(value: str) -> str:
    return re.sub(r"(?:\s+(?:NEW|새글|첨부파일))+$", "", value).strip()


def _normalize_spaces(value: str) -> str:
    return " ".join(value.split())
