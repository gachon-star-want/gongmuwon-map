from __future__ import annotations

from datetime import date
from uuid import uuid4

import httpx
import pytest

from public_officer_pipeline.artifact import artifact_from_response
from public_officer_pipeline.models import PostRef
from public_officer_pipeline.storage import (
    NullSourceStorage,
    R2SourceStorage,
    SourceStorageError,
)


class _FakeS3Client:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def put_object(self, **kwargs: object) -> None:
        self.calls.append(kwargs)


def _post_ref(**kwargs) -> PostRef:
    values = {
        "agency_id": uuid4(),
        "url": "https://example.com/expense/1",
        "title": "테스트 내역",
        "published_at": None,
        "department_name": "행정지원과",
        "file_kind": "html",
    }
    values.update(kwargs)
    return PostRef(**values)


def test_r2_put_artifact_generates_expected_r2_path() -> None:
    response = httpx.Response(
        200,
        content="테스트 공문".encode("utf-8"),
        request=httpx.Request("GET", "https://example.com/expense/1"),
    )
    artifact = artifact_from_response(
        _post_ref(agency_id=uuid4(), published_at=date(2026, 5, 1)),
        response,
    )

    client = _FakeS3Client()
    storage = R2SourceStorage(client=client, bucket="officer-map-raw")
    storage_path = storage.put_artifact(artifact)

    assert storage_path.startswith("r2://officer-map-raw/")
    key = client.calls[0]["Key"]
    assert key.startswith(f"{artifact.agency_id}/2026-05/")
    assert key.endswith(f"{artifact.hash_sha256}.html")
    assert storage_path == f"r2://officer-map-raw/{key}"
    metadata = client.calls[0]["Metadata"]
    assert metadata["agency_id"] == str(artifact.agency_id)
    assert metadata["hash_sha256"] == artifact.hash_sha256


def test_r2_put_artifact_uploads_html_as_utf8_bytes() -> None:
    response = httpx.Response(
        200,
        content="<meta charset=\"utf-8\">안녕하세요".encode("utf-8"),
        request=httpx.Request("GET", "https://example.com/expense/1"),
    )
    artifact = artifact_from_response(_post_ref(file_kind="html"), response)

    client = _FakeS3Client()
    storage = R2SourceStorage(client=client, bucket="officer-map-raw")
    storage.put_artifact(artifact)

    assert client.calls[0]["Body"] == response.text.encode("utf-8")


def test_r2_put_artifact_uploads_binary_bytes() -> None:
    response = httpx.Response(
        200,
        content=b"\x01\x02\x03\x04\x05",
        request=httpx.Request("GET", "https://example.com/expense/1"),
    )
    artifact = artifact_from_response(_post_ref(file_kind="pdf"), response)

    client = _FakeS3Client()
    storage = R2SourceStorage(client=client, bucket="officer-map-raw")
    storage.put_artifact(artifact)

    assert client.calls[0]["Body"] == response.content


def test_r2_from_env_requires_required_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("R2_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("R2_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("R2_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("R2_BUCKET", raising=False)

    with pytest.raises(SourceStorageError, match="missing required R2 env vars"):
        R2SourceStorage.from_env()


def test_r2_put_artifact_requires_content_or_html() -> None:
    artifact = artifact_from_response(_post_ref(file_kind="pdf"), httpx.Response(
        200,
        content=b"blob",
        request=httpx.Request("GET", "https://example.com/expense/1"),
    ))
    artifact.content_bytes = None
    artifact.html = ""

    client = _FakeS3Client()
    storage = R2SourceStorage(client=client, bucket="officer-map-raw")

    with pytest.raises(SourceStorageError, match="no content"):
        storage.put_artifact(artifact)


def test_null_source_storage_returns_none() -> None:
    artifact = artifact_from_response(_post_ref(), httpx.Response(
        200,
        content="hello".encode("utf-8"),
        request=httpx.Request("GET", "https://example.com/expense/1"),
    ))
    storage = NullSourceStorage()

    assert storage.put_artifact(artifact) is None
