from __future__ import annotations

import re
from datetime import date
from typing import Any

import httpx

from public_officer_pipeline.artifact import artifact_from_response, post_detail_from_artifact
from public_officer_pipeline.models import Agency, PostDetail, PostRef
from public_officer_pipeline.source_pattern import AlioItemDisclosurePattern, parse_source_pattern


DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
DEFAULT_USER_AGENT = (
    "PublicOfficerMapBot/0.1 "
    "(operator: wylee0806@naver.com; public-interest archive)"
)


class AlioItemDisclosureCrawler:
    def __init__(
        self,
        agency: Agency,
        client: httpx.AsyncClient | None = None,
        source_pattern: AlioItemDisclosurePattern | None = None,
    ) -> None:
        self.agency = agency
        pattern = source_pattern or parse_source_pattern(self.agency)
        if not isinstance(pattern, AlioItemDisclosurePattern):
            raise ValueError("AlioItemDisclosureCrawler requires an ALIO item disclosure pattern")
        self.pattern = pattern
        self.file_kinds = set(pattern.fileKinds)
        self._client = client or httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": pattern.sourceUrl,
            },
        )
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def list_posts(self, since: date, limit_pages: int = 3) -> list[PostRef]:
        _ = limit_pages
        if self.pattern.directFiles:
            return self._direct_file_refs(since=since)
        row = await self._agency_disclosure_row()
        if row is None:
            return []

        disclosure_no = str(row.get("disclosureNo") or "").strip()
        if not disclosure_no:
            return []

        published_at = _date_from_disclosure_no(disclosure_no)
        refs: list[PostRef] = []
        for file_no, filename in _parse_files(str(row.get("files") or "")):
            file_kind = _file_kind(filename)
            if file_kind not in self.file_kinds:
                continue
            file_year = _file_year(filename)
            if file_year is not None and file_year < since.year:
                continue
            refs.append(
                PostRef(
                    agency_id=self.agency.id,
                    url=str(
                        httpx.URL(self.pattern.downloadUrl).copy_merge_params(
                            {"f": file_no, "d": disclosure_no}
                        )
                    ),
                    title=f"ALIO 기관장 업무추진비 - {self.agency.short_name} - {filename}",
                    published_at=published_at,
                    department_name=self.agency.short_name,
                    file_kind=file_kind,
                )
            )
        return refs

    def _direct_file_refs(self, *, since: date) -> list[PostRef]:
        refs: list[PostRef] = []
        for item in self.pattern.directFiles:
            file_no = str(item.get("fileNo") or "").strip()
            disclosure_no = str(item.get("disclosureNo") or "").strip()
            filename = str(item.get("filename") or "").strip()
            if not file_no or not disclosure_no or not filename:
                continue
            file_kind = _file_kind(filename)
            if file_kind not in self.file_kinds:
                continue
            file_year = _file_year(filename)
            if file_year is not None and file_year < since.year:
                continue
            published_at = _date_from_direct_file(item) or _date_from_disclosure_no(disclosure_no)
            refs.append(
                PostRef(
                    agency_id=self.agency.id,
                    url=str(
                        httpx.URL(self.pattern.downloadUrl).copy_merge_params(
                            {"f": file_no, "d": disclosure_no}
                        )
                    ),
                    title=f"ALIO 기관장 업무추진비 - {self.agency.short_name} - {filename}",
                    published_at=published_at,
                    department_name=self.agency.short_name,
                    file_kind=file_kind,
                )
            )
        return refs

    async def fetch_post(self, ref: PostRef) -> PostDetail:
        response = await self._client.get(ref.url, headers={"Referer": self.pattern.sourceUrl})
        response.raise_for_status()
        return post_detail_from_artifact(artifact_from_response(ref, response))

    async def _agency_disclosure_row(self) -> dict[str, Any] | None:
        payload = {
            "reportFormRootNo": self.pattern.reportFormRootNo,
            "quart": "",
            "apbaType": [],
            "jidtDptm": [],
            "area": [],
            "apbaId": "",
        }
        response = await self._client.post(self.pattern.listUrl, json=payload)
        response.raise_for_status()
        data = response.json()
        rows = data.get("data", {}).get("organList", [])
        if not isinstance(rows, list):
            return None
        for row in rows:
            if not isinstance(row, dict):
                continue
            if str(row.get("apbaNa") or "").strip() == self.pattern.alioAgencyName:
                return row
        return None


def _parse_files(value: str) -> list[tuple[str, str]]:
    files: list[tuple[str, str]] = []
    for item in value.split("|"):
        if "@" not in item:
            continue
        file_no, filename = item.split("@", 1)
        file_no = file_no.strip()
        filename = filename.strip()
        if file_no and filename:
            files.append((file_no, filename))
    return files


def _file_kind(filename: str) -> str:
    match = re.search(r"\.([a-zA-Z0-9]+)\s*$", filename)
    return match.group(1).lower() if match else "html"


def _file_year(filename: str) -> int | None:
    full_year = re.search(r"(20\d{2})", filename)
    if full_year:
        return int(full_year.group(1))
    short_year = re.search(r"(?<!\d)(\d{2})\s*년", filename)
    if short_year:
        year = int(short_year.group(1))
        return 2000 + year if year < 70 else 1900 + year
    return None


def _date_from_disclosure_no(disclosure_no: str) -> date | None:
    match = re.match(r"^(20\d{2})(\d{2})(\d{2})", disclosure_no)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def _date_from_direct_file(item: dict[str, str]) -> date | None:
    raw = str(item.get("publishedAt") or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


__all__ = ["AlioItemDisclosureCrawler"]
