from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
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
        command = [
            "curl",
            "-sS",
            "--compressed",
            "-D-",
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
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            if process.returncode == 63:
                raise guards.DocumentProcessingLimitError(
                    f"downloaded document exceeds limit of {self._max_download_bytes} bytes"
                )
            raise httpx.RequestError(
                stderr.decode("utf-8", errors="replace") if stderr else "curl request failed",
                request=request,
            )

        status_code, body_bytes, headers = self._parse_curl_output(stdout)
        guards.ensure_content_length_at_most(
            headers,
            max_bytes=self._max_download_bytes,
            subject="downloaded document",
        )
        guards.ensure_size_at_most(
            size=len(body_bytes),
            max_bytes=self._max_download_bytes,
            subject="downloaded document body",
        )
        text = _decode_response_text(body_bytes, headers)

        return SimpleHttpResponse(
            status_code=status_code,
            content=body_bytes,
            text=text,
            headers=headers,
            url=request_url,
        )

    def _parse_curl_output(self, data: bytes) -> tuple[int, bytes, dict[str, str]]:
        match = list(re.finditer(rb"(?m)^HTTP/\S+\s+\d{3}.*$", data))
        if not match:
            return 200, data, {}

        latest = match[-1]
        header_start = latest.start()
        header_end = data.find(b"\r\n\r\n", header_start)
        if header_end == -1:
            return 500, data[header_start:], {}

        raw_headers = data[header_start:header_end].decode("iso-8859-1", errors="replace")
        status_code = _parse_status_from_headers(raw_headers)
        headers = _parse_httpx_like_headers(raw_headers)
        remaining = data[header_end + 4 :]
        body = remaining
        return status_code, body, headers

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
