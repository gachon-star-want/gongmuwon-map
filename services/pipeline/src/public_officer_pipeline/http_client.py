from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
from typing import Any

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx


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
    ) -> None:
        self._headers = headers
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=headers,
            follow_redirects=follow_redirects,
        )

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> SimpleHttpResponse:
        response = await self._client.get(url, params=params, headers=_merge_headers(self._headers, headers), **kwargs)
        return SimpleHttpResponse(
            status_code=response.status_code,
            text=response.text,
            content=response.content,
            headers=dict(response.headers),
            url=str(response.url),
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
    ) -> None:
        self._timeout = timeout
        self._headers = headers
        self._follow_redirects = follow_redirects
        self._doh_url = doh_url

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
            raise httpx.RequestError(
                stderr.decode("utf-8", errors="replace") if stderr else "curl request failed",
                request=request,
            )

        status_code, body_bytes, headers = self._parse_curl_output(stdout)
        try:
            text = body_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = body_bytes.decode("cp949", errors="replace")

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
