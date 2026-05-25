from __future__ import annotations

import hashlib
from datetime import date
from uuid import uuid4

import httpx
import pytest

from public_officer_pipeline.artifact import artifact_from_response, post_detail_from_artifact
from public_officer_pipeline.crawler.gangnam import GangnamExpenseCrawler
from public_officer_pipeline.models import PostDetail, PostRef


def _post_ref(**kwargs) -> PostRef:
    values = {
        "agency_id": uuid4(),
        "url": "https://example.com/expense/1",
        "title": "테스트 내역",
        "published_at": date(2026, 5, 1),
        "department_name": "행정지원과",
        "file_kind": "html",
    }
    values.update(kwargs)
    return PostRef(**values)


def test_artifact_stable_hash_for_same_html() -> None:
    ref = _post_ref()
    response = httpx.Response(
        200,
        content="테스트 공문 내용".encode("utf-8"),
        request=httpx.Request("GET", "https://example.com/expense/1"),
        headers={"content-type": "text/html; charset=utf-8"},
    )

    first = artifact_from_response(ref, response)
    second = artifact_from_response(ref, response)

    assert first.hash_sha256 == second.hash_sha256
    assert first.hash_sha256 == hashlib.sha256(response.text.encode("utf-8")).hexdigest()


def test_artifact_stable_hash_for_same_binary() -> None:
    content = b"\x01\x02\x03\x04\x05"
    ref = _post_ref(file_kind="pdf")
    response = httpx.Response(
        200,
        content=content,
        request=httpx.Request("GET", "https://example.com/expense/1"),
    )

    first = artifact_from_response(ref, response)
    second = artifact_from_response(ref, response)

    assert first.hash_sha256 == second.hash_sha256
    assert first.hash_sha256 == hashlib.sha256(content).hexdigest()


def test_artifact_preserves_metadata_from_post_ref() -> None:
    ref = _post_ref(file_kind="pdf")
    response = httpx.Response(
        200,
        content=b"abc",
        request=httpx.Request("GET", "https://example.com/expense/1"),
    )

    artifact = artifact_from_response(ref, response)

    assert artifact.agency_id == ref.agency_id
    assert artifact.url == ref.url
    assert artifact.title == ref.title
    assert artifact.published_at == ref.published_at
    assert artifact.department_name == ref.department_name
    assert artifact.file_kind == ref.file_kind
    assert artifact.storage_path is None


def test_post_detail_from_artifact_discards_storage_path() -> None:
    ref = _post_ref(file_kind="pdf")
    response = httpx.Response(
        200,
        content=b"abc",
        request=httpx.Request("GET", "https://example.com/expense/1"),
    )

    artifact = artifact_from_response(ref, response)
    artifact.storage_path = "r2://officer-map-raw/1234/2026-05/example.bin"

    detail = post_detail_from_artifact(artifact)

    assert detail.model_dump().get("storage_path", None) is None
    assert detail.url == artifact.url
    assert detail.hash_sha256 == artifact.hash_sha256


class _FakeClient:
    def __init__(self, response: httpx.Response) -> None:
        self._response = response

    async def get(self, _url: str) -> httpx.Response:  # pragma: no cover - thin adapter
        return self._response

    async def aclose(self) -> None:  # pragma: no cover - thin adapter
        return None


@pytest.mark.asyncio
async def test_gangnam_fetch_post_prefers_header_file_kind() -> None:
    response = httpx.Response(
        200,
        content=b"binary",
        request=httpx.Request("GET", "https://www.gangnam.go.kr/file/1/get/test"),
        headers={"content-disposition": "attachment; filename=\"expense_report.xls\""},
    )
    crawler = GangnamExpenseCrawler(client=_FakeClient(response))
    ref = _post_ref(
        agency_id=uuid4(),
        url="https://www.gangnam.go.kr/file/1/get/test",
        file_kind="html",
    )

    detail = await crawler.fetch_post(ref)

    assert isinstance(detail, PostDetail)
    assert detail.file_kind == "xls"
    assert detail.hash_sha256 == hashlib.sha256(response.content).hexdigest()
    assert detail.content_bytes == response.content
