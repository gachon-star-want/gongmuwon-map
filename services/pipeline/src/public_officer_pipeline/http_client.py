from __future__ import annotations

import asyncio
from contextlib import suppress
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from public_officer_pipeline import document_guards as guards


Backend = {"auto", "httpx", "curl"}


def _resolve_timeout_seconds(timeout: httpx.Timeout | float | None) -> float:
    if isinstance(timeout, httpx.Timeout):
        return float(timeout.connect or timeout.read or 30.0)
    if isinstance(timeout, (int, float)):
        return float(timeout)
    return 30.0


def _build_url_with_params(url: str, params: dict[str, Any] | None) -> str:
    if not params:
        return url
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    for key, value in params.items():
        if value is None:
            continue
        query[str(key)] = str(value)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _parse_status_from_headers(header_text: str) -> int:
    match = re.search(r"HTTP/\S+\s+(\d{3})", header_text)
    return int(match.group(1)) if match else 200


def _parse_httpx_like_headers(raw_headers: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in raw_headers.splitlines():
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers[name.strip()] = value.strip()
    return headers


def _merge_headers(base: dict[str, str], extra: dict[str, str] | None) -> dict[str, str]:
    if not extra:
        return dict(base)
    merged = dict(base)
    merged.update(extra)
    return merged


def _parse_curl_header_file(data: bytes) -> tuple[int, dict[str, str]]:
    header_text = data.decode("iso-8859-1", errors="replace")
    blocks = [block.strip() for block in re.split(r"\r?\n\r?\n", header_text) if block.strip()]
    http_blocks = [
        block
        for block in blocks
        if re.match(r"^HTTP/\S+\s+\d{3}\b", block.splitlines()[0])
    ]
    if not http_blocks:
        return 200, {}

    final_block = http_blocks[-1]
    return _parse_status_from_headers(final_block), _parse_httpx_like_headers(final_block)


async def _communicate_with_output_file_limit(
    process: asyncio.subprocess.Process,
    *,
    output_path: Path,
    max_bytes: int,
    subject: str,
) -> tuple[bytes | None, bytes | None]:
    task = asyncio.create_task(process.communicate())
    try:
        while not task.done():
            if output_path.exists():
                guards.ensure_size_at_most(
                    size=output_path.stat().st_size,
                    max_bytes=max_bytes,
                    subject=subject,
                )
            await asyncio.sleep(0.05)
        stdout, stderr = await task
        if output_path.exists():
            guards.ensure_size_at_most(
                size=output_path.stat().st_size,
                max_bytes=max_bytes,
                subject=subject,
            )
        return stdout, stderr
    except guards.DocumentProcessingLimitError:
        if not task.done():
            kill = getattr(process, "kill", None)
            if callable(kill):
                kill()
            with suppress(Exception):
                await task
        raise


def _decode_response_text(content: bytes, headers: dict[str, str]) -> str:
    try:
        response = httpx.Response(200, headers=headers, content=content)
        return response.text
    except UnicodeDecodeError:
        return content.decode("cp949", errors="replace")


@dataclass
class SimpleHttpResponse:
    status_code: int
    text: str
    content: bytes
    headers: dict[str, str]
    url: str

    def raise_for_status(self) -> None:
        if self.status_code < 400:
            return
        request = httpx.Request("GET", self.url)
        response = httpx.Response(
            status_code=self.status_code,
            headers=self.headers,
            content=self.content,
            request=request,
        )
        raise httpx.HTTPStatusError(f"HTTP status {self.status_code}", request=request, response=response)


class AsyncHttpClient:
    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **_: Any,
    ) -> SimpleHttpResponse:
        raise NotImplementedError

    async def aclose(self) -> None:
        raise NotImplementedError


class _HttpxClient(AsyncHttpClient):
    def __init__(
        self,
        *,
        timeout: httpx.Timeout,
        headers: dict[str, str],
        follow_redirects: bool,
        max_download_bytes: int = guards.MAX_DOCUMENT_DOWNLOAD_BYTES,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._headers = headers
        self._max_download_bytes = max_download_bytes
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=headers,
            follow_redirects=follow_redirects,
            transport=transport,
        )

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> SimpleHttpResponse:
        async with self._client.stream(
            "GET",
            url,
            params=params,
            headers=_merge_headers(self._headers, headers),
            **kwargs,
        ) as response:
            response_headers = dict(response.headers)
            guards.ensure_content_length_at_most(
                response_headers,
                max_bytes=self._max_download_bytes,
                subject="downloaded document",
            )
            chunks: list[bytes] = []
            total_size = 0
            async for chunk in response.aiter_bytes():
                total_size += len(chunk)
                guards.ensure_size_at_most(
                    size=total_size,
                    max_bytes=self._max_download_bytes,
                    subject="downloaded document body",
                )
                chunks.append(chunk)
            content = b"".join(chunks)
            text = _decode_response_text(content, response_headers)
            status_code = response.status_code
            response_url = str(response.url)
        return SimpleHttpResponse(
            status_code=status_code,
            text=text,
            content=content,
            headers=response_headers,
            url=response_url,
        )

    async def aclose(self) -> None:
        await self._client.aclose()


class _CurlClient(AsyncHttpClient):
    def __init__(
        self,
        *,
        timeout: float,
        headers: dict[str, str],
        follow_redirects: bool,
        doh_url: str | None = None,
        max_download_bytes: int = guards.MAX_DOCUMENT_DOWNLOAD_BYTES,
    ) -> None:
        self._timeout = timeout
        self._headers = headers
        self._follow_redirects = follow_redirects
        self._doh_url = doh_url
        self._max_download_bytes = max_download_bytes

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **_: Any,
    ) -> SimpleHttpResponse:
        request_url = _build_url_with_params(url, params)
        request = httpx.Request("GET", request_url)
        with tempfile.TemporaryDirectory() as directory:
            header_path = Path(directory) / "headers.txt"
            body_path = Path(directory) / "body.bin"
            command = [
                "curl",
                "-sS",
                "--compressed",
                "-D",
                str(header_path),
                "-o",
                str(body_path),
                "--max-time",
                str(int(self._timeout)),
                "--connect-timeout",
                str(int(self._timeout)),
                "--retry", "0",
                "--max-filesize",
                str(self._max_download_bytes),
            ]
            if self._doh_url:
                command.extend(["--doh-url", self._doh_url])
            if self._follow_redirects:
                command.append("-L")
            for key, value in _merge_headers(self._headers, headers).items():
                command.extend(["-H", f"{key}: {value}"])
            command.append(request_url)

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await _communicate_with_output_file_limit(
                process,
                output_path=body_path,
                max_bytes=self._max_download_bytes,
                subject="downloaded document body",
            )
            if process.returncode != 0:
                if process.returncode == 63:
                    raise guards.DocumentProcessingLimitError(
                        f"downloaded document exceeds limit of {self._max_download_bytes} bytes"
                    )
                raise httpx.RequestError(
                    stderr.decode("utf-8", errors="replace") if isinstance(stderr, bytes) and stderr else "curl request failed",
                    request=request,
                )

            header_bytes = header_path.read_bytes() if header_path.exists() else b""
            status_code, headers = _parse_curl_header_file(header_bytes)
            guards.ensure_content_length_at_most(
                headers,
                max_bytes=self._max_download_bytes,
                subject="downloaded document",
            )
            body_size = body_path.stat().st_size if body_path.exists() else 0
            guards.ensure_size_at_most(
                size=body_size,
                max_bytes=self._max_download_bytes,
                subject="downloaded document body",
            )
            body_bytes = body_path.read_bytes() if body_path.exists() else b""
            text = _decode_response_text(body_bytes, headers)

        return SimpleHttpResponse(
            status_code=status_code,
            content=body_bytes,
            text=text,
            headers=headers,
            url=request_url,
        )

    async def aclose(self) -> None:
        return None


class _AdaptiveHttpClient(AsyncHttpClient):
    def __init__(
        self,
        timeout: httpx.Timeout,
        headers: dict[str, str],
        follow_redirects: bool,
    ) -> None:
        self._primary = _HttpxClient(timeout=timeout, headers=headers, follow_redirects=follow_redirects)
        fallback_timeout = _resolve_timeout_seconds(timeout)
        doh_url = os.getenv("PIPELINE_CURL_DOH_URL", "").strip() or None
        self._fallback = _CurlClient(
            timeout=fallback_timeout,
            headers=headers,
            follow_redirects=follow_redirects,
            doh_url=doh_url,
        )

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> SimpleHttpResponse:
        try:
            return await self._primary.get(url, params=params, headers=headers, **kwargs)
        except (httpx.ConnectError, httpx.NetworkError, httpx.TimeoutException, OSError):
            return await self._fallback.get(url, params=params, headers=headers, **kwargs)

    async def aclose(self) -> None:
        await self._primary.aclose()


def create_http_client(
    *,
    timeout: httpx.Timeout,
    headers: dict[str, str],
    follow_redirects: bool,
) -> AsyncHttpClient:
    backend = os.getenv("PIPELINE_HTTP_BACKEND", "auto").strip().lower()
    if backend not in Backend:
        backend = "auto"
    if backend == "curl":
        doh_url = os.getenv("PIPELINE_CURL_DOH_URL", "").strip() or None
        return _CurlClient(
            timeout=_resolve_timeout_seconds(timeout),
            headers=headers,
            follow_redirects=follow_redirects,
            doh_url=doh_url,
        )
    if backend == "httpx":
        return _HttpxClient(timeout=timeout, headers=headers, follow_redirects=follow_redirects)
    return _AdaptiveHttpClient(timeout=timeout, headers=headers, follow_redirects=follow_redirects)
