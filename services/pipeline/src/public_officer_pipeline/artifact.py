from __future__ import annotations

from datetime import date, datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from public_officer_pipeline.models import PostDetail, PostRef


class SourceArtifact(BaseModel):
    agency_id: UUID
    url: str
    title: str
    published_at: date | None
    department_name: str | None
    file_kind: str
    html: str = ""
    content_bytes: bytes | None = None
    fetched_at: datetime
    hash_sha256: str
    storage_path: str | None = None


def _hash_content(content: bytes) -> str:
    return sha256(content).hexdigest()


def artifact_from_response(
    ref: PostRef,
    response: Any,
    *,
    fallback_file_kind: str | None = None,
) -> SourceArtifact:
    file_kind = fallback_file_kind or ref.file_kind
    if file_kind == "html":
        html = response.text
        content_bytes = None
        text_for_hash = html.encode("utf-8")
    else:
        html = ""
        content_bytes = response.content
        text_for_hash = content_bytes

    return SourceArtifact(
        agency_id=ref.agency_id,
        url=ref.url,
        title=ref.title,
        published_at=ref.published_at,
        department_name=ref.department_name,
        file_kind=file_kind,
        html=html,
        content_bytes=content_bytes,
        fetched_at=datetime.now(timezone.utc),
        hash_sha256=_hash_content(text_for_hash),
    )


def post_detail_from_artifact(artifact: SourceArtifact) -> PostDetail:
    return PostDetail(
        **artifact.model_dump(exclude={"storage_path"}),
    )
