from __future__ import annotations

import ast
import json
import re
from datetime import date
from typing import Any

import httpx

from public_officer_pipeline import document_guards as guards
from public_officer_pipeline.artifact import artifact_from_response, post_detail_from_artifact
from public_officer_pipeline.models import Agency, PostDetail, PostRef
from public_officer_pipeline.source_pattern import CleanEyeOwnerWorkCostPattern, parse_source_pattern


DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
DEFAULT_USER_AGENT = (
    "PublicOfficerMapBot/0.1 "
    "(operator: wylee0806@naver.com; public-interest archive)"
)
JSON_LIST_RE = re.compile(r"var\s+jsonListQ\s*=\s*(?P<literal>'(?:\\.|[^'])*')\s*;", re.DOTALL)


class CleanEyeOwnerWorkCostCrawler:
    def __init__(
        self,
        agency: Agency,
        client: httpx.AsyncClient | None = None,
        source_pattern: CleanEyeOwnerWorkCostPattern | None = None,
    ) -> None:
        self.agency = agency
        pattern = source_pattern or parse_source_pattern(self.agency)
        if not isinstance(pattern, CleanEyeOwnerWorkCostPattern):
            raise ValueError("CleanEyeOwnerWorkCostCrawler requires a CleanEye owner work cost pattern")
        self.pattern = pattern
        self.file_kinds = set(pattern.fileKinds)
        self._download_params_by_url: dict[str, dict[str, str]] = {}
        self._client = client or httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/json,*/*; q=0.8",
            },
        )
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def list_posts(self, since: date, limit_pages: int = 3) -> list[PostRef]:
        _ = limit_pages
        detail_url = self._detail_url()
        response = await self._client.get(detail_url, headers={"Referer": self.pattern.sourceUrl})
        response.raise_for_status()
        rows = _parse_json_list_q(response.text)
        refs: list[PostRef] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            ref = self._post_ref_from_row(row, since=since)
            if ref is not None:
                refs.append(ref)
        return refs

    async def fetch_post(self, ref: PostRef) -> PostDetail:
        params = self._download_params_by_url.get(ref.url) or _download_params_from_url(ref.url)
        exists = await self._client.post(
            self.pattern.fileExistsUrl,
            data=params,
            headers={"Referer": self._detail_url()},
        )
        exists.raise_for_status()
        if exists.json().get("msg") != "SUCCESS":
            raise httpx.HTTPStatusError(
                "CleanEye fileExists did not return SUCCESS",
                request=exists.request,
                response=exists,
            )

        response = await self._client.post(
            self.pattern.downloadUrl,
            data=params,
            headers={"Referer": self._detail_url()},
        )
        response.raise_for_status()
        guards.ensure_size_at_most(
            size=len(response.content),
            max_bytes=guards.MAX_DOCUMENT_DOWNLOAD_BYTES,
            subject="cleaneye document",
        )
        return post_detail_from_artifact(artifact_from_response(ref, response))

    def _post_ref_from_row(self, row: dict[str, Any], *, since: date) -> PostRef | None:
        filename = str(row.get("filename") or "").strip()
        upload_filename = str(row.get("saveFileName") or "").strip()
        file_path = str(row.get("filePath") or "").strip()
        file_kind = _file_kind(filename or upload_filename)
        if file_kind not in self.file_kinds:
            return None
        if not filename or not upload_filename or not file_path:
            return None

        file_year = _file_year(row, filename=filename, upload_filename=upload_filename)
        if file_year is not None and file_year < since.year:
            return None

        params = {
            "UPLOAD_FILENAME": upload_filename,
            "ORIGINAL_FILENAME": filename,
            "FILE_PATH": file_path,
        }
        url = str(httpx.URL(self.pattern.downloadUrl).copy_merge_params(params))
        self._download_params_by_url[url] = params
        published_at = _date_from_upload_filename(upload_filename)
        quarter = str(row.get("dtFlagName") or row.get("costQuarter") or "").strip()
        title = f"CleanEye 기관장 업무추진비 - {self.agency.short_name}"
        if quarter:
            title = f"{title} - {file_year or ''} {quarter}".strip()
        return PostRef(
            agency_id=self.agency.id,
            url=url,
            title=title,
            published_at=published_at,
            department_name=self.agency.short_name,
            file_kind=file_kind,
        )

    def _detail_url(self) -> str:
        return str(httpx.URL(self.pattern.sourceUrl).copy_merge_params(self._detail_params()))

    def _detail_params(self) -> dict[str, str]:
        fixed_year = self.pattern.fixedYear
        return {
            "entId": self.pattern.entId,
            "entKind": self.pattern.entKind,
            "entName": self.pattern.entName,
            "itemId": self.pattern.itemId,
            "fixedYear": str(fixed_year),
            "beyondYear": str(self.pattern.beyondYear or fixed_year + 4),
            "budgetSumYear": str(self.pattern.budgetSumYear or fixed_year + 1),
            "pastYear": str(self.pattern.pastYear or fixed_year - 4),
            "fixedQuarterYear": str(self.pattern.fixedQuarterYear or fixed_year),
            "pastQuarterYear": str(self.pattern.pastQuarterYear or fixed_year - 4),
            "fixedHalfYear": str(self.pattern.fixedHalfYear or fixed_year),
            "pastHalfYear": str(self.pattern.pastHalfYear or fixed_year - 4),
            "dtFlagQuarter": self.pattern.dtFlagQuarter,
            "dtFlagHalf": self.pattern.dtFlagHalf,
        }


def _parse_json_list_q(html: str) -> list[dict[str, Any]]:
    match = JSON_LIST_RE.search(html)
    if not match:
        return []
    try:
        json_text = ast.literal_eval(match.group("literal"))
        data = json.loads(json_text)
    except (SyntaxError, ValueError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _file_kind(filename: str) -> str:
    match = re.search(r"\.([a-zA-Z0-9]+)\s*$", filename)
    return match.group(1).lower() if match else "html"


def _file_year(row: dict[str, Any], *, filename: str, upload_filename: str) -> int | None:
    accyear = str(row.get("accyear") or "").strip()
    if re.fullmatch(r"20\d{2}", accyear):
        return int(accyear)
    for value in (filename, upload_filename):
        match = re.search(r"(20\d{2})", value)
        if match:
            return int(match.group(1))
    return None


def _date_from_upload_filename(upload_filename: str) -> date | None:
    match = re.match(r"^(20\d{2})(\d{2})(\d{2})", upload_filename)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def _download_params_from_url(url: str) -> dict[str, str]:
    parsed = httpx.URL(url)
    params = dict(parsed.params.multi_items())
    return {
        "UPLOAD_FILENAME": params.get("UPLOAD_FILENAME", ""),
        "ORIGINAL_FILENAME": params.get("ORIGINAL_FILENAME", ""),
        "FILE_PATH": params.get("FILE_PATH", ""),
    }


__all__ = ["CleanEyeOwnerWorkCostCrawler"]
