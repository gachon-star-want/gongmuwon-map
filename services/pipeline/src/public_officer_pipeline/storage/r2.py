from __future__ import annotations

import os
from datetime import date
from typing import Any, Protocol

from public_officer_pipeline.artifact import SourceArtifact


class SourceStorageError(RuntimeError):
    """Raised when source artifact persistence fails."""


class SourceStorage(Protocol):
    def put_artifact(self, artifact: SourceArtifact) -> str | None: ...


class R2SourceStorage:
    def __init__(self, *, client: Any, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    @classmethod
    def from_env(cls, *, prefix: str = "R2") -> "R2SourceStorage":
        names = {
            "account_id": f"{prefix}_ACCOUNT_ID",
            "access_key_id": f"{prefix}_ACCESS_KEY_ID",
            "secret_access_key": f"{prefix}_SECRET_ACCESS_KEY",
            "bucket": f"{prefix}_BUCKET",
        }
        account_id = os.getenv(names["account_id"])
        access_key_id = os.getenv(names["access_key_id"])
        secret_access_key = os.getenv(names["secret_access_key"])
        bucket = os.getenv(names["bucket"])

        missing = [name for name, value in {
            names["account_id"]: account_id,
            names["access_key_id"]: access_key_id,
            names["secret_access_key"]: secret_access_key,
            names["bucket"]: bucket,
        }.items() if not value]

        if missing:
            raise SourceStorageError(
                "missing required R2 env vars: " + ", ".join(missing)
            )

        try:
            import boto3  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise SourceStorageError("boto3 is required for R2 uploads") from exc

        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        client = boto3.client(  # type: ignore[attr-defined]
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )
        return cls(client=client, bucket=bucket)

    def put_artifact(self, artifact: SourceArtifact) -> str:
        key = self._artifact_key(artifact)
        body = artifact.content_bytes
        if body is None:
            if artifact.html == "":
                raise SourceStorageError("artifact has no content bytes and empty html")
            body = artifact.html.encode("utf-8")

        metadata = {
            "agency_id": str(artifact.agency_id),
            "source_url": artifact.url,
            "source_title": artifact.title,
            "hash_sha256": artifact.hash_sha256,
        }
        if artifact.published_at:
            metadata["published_at"] = artifact.published_at.isoformat()

        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=body,
                Metadata=metadata,
            )
        except Exception as exc:  # pragma: no cover
            raise SourceStorageError("failed to upload source artifact to R2") from exc

        return f"r2://{self._bucket}/{key}"

    @staticmethod
    def _artifact_month(artifact: SourceArtifact) -> str:
        source_date: date = artifact.published_at or artifact.fetched_at.date()
        return source_date.strftime("%Y-%m")

    def _artifact_key(self, artifact: SourceArtifact) -> str:
        artifact_month = self._artifact_month(artifact)
        return f"{artifact.agency_id}/{artifact_month}/{artifact.hash_sha256}.{artifact.file_kind}"


class NullSourceStorage:
    def put_artifact(self, _artifact: SourceArtifact) -> None:
        return None
