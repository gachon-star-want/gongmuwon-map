from pathlib import Path

import httpx
import pytest

from public_officer_pipeline import document_guards as guards
from public_officer_pipeline.http_client import (
    _AdaptiveHttpClient,
    _CurlClient,
    _HttpxClient,
    _build_url_with_params,
    _parse_curl_header_file,
    create_http_client,
)


def test_build_url_with_params_keeps_existing_query_values() -> None:
    assert (
        _build_url_with_params("https://example.com/search?year=2026", {"page": 3})
        == "https://example.com/search?year=2026&page=3"
    )


def _write_curl_files(
    args: tuple[object, ...],
    *,
    header_bytes: bytes = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n",
    body_bytes: bytes = b"ok",
) -> None:
    command = [str(item) for item in args]
    Path(command[command.index("-D") + 1]).write_bytes(header_bytes)
    Path(command[command.index("-o") + 1]).write_bytes(body_bytes)


def test_curl_header_parser_prefers_last_http_response() -> None:
    raw_headers = (
        "HTTP/1.1 301 Moved\r\nLocation: /legacy\r\n\r\n"
        "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
    ).encode("utf-8")

    status_code, headers = _parse_curl_header_file(raw_headers)

    assert status_code == 200
    assert headers == {"Content-Type": "text/plain"}


@pytest.mark.asyncio
async def test_curl_client_does_not_scan_binary_body_for_http_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binary_body = b"%PDF-1.4\nHTTP/1.1 500 fake\r\n\r\nbody"

    async def fake_subprocess_exec(*args: object, **_kwargs: object):
        _write_curl_files(
            args,
            header_bytes=b"HTTP/1.1 200 OK\r\nContent-Type: application/pdf\r\n\r\n",
            body_bytes=binary_body,
        )

        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", b""

        return DummyProcess()

    monkeypatch.setattr(
        "public_officer_pipeline.http_client.asyncio.create_subprocess_exec",
        fake_subprocess_exec,
    )

    client = _CurlClient(timeout=1.0, headers={}, follow_redirects=False)
    response = await client.get("https://example.com/file.pdf")

    assert response.status_code == 200
    assert response.content == binary_body
    assert response.headers == {"Content-Type": "application/pdf"}


@pytest.mark.asyncio
async def test_curl_client_decodes_text_when_non_ascii_headers_are_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_subprocess_exec(*args: object, **_kwargs: object):
        _write_curl_files(
            args,
            header_bytes=(
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                "Content-Disposition: attachment; filename=\"업무추진비.pdf\"\r\n"
                "\r\n"
            ).encode(),
            body_bytes="업무추진비".encode(),
        )

        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", b""

        return DummyProcess()

    monkeypatch.setattr(
        "public_officer_pipeline.http_client.asyncio.create_subprocess_exec",
        fake_subprocess_exec,
    )

    client = _CurlClient(timeout=1.0, headers={}, follow_redirects=False)
    response = await client.get("https://example.com/file.pdf")

    assert response.status_code == 200
    assert response.text == "업무추진비"
    assert "Content-Disposition" in response.headers


@pytest.mark.asyncio
async def test_curl_client_ignores_content_encoding_after_compressed_download(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_subprocess_exec(*args: object, **_kwargs: object):
        _write_curl_files(
            args,
            header_bytes=(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/html; charset=utf-8\r\n"
                b"Content-encoding: gzip\r\n"
                b"\r\n"
            ),
            body_bytes=b"already decoded",
        )

        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", b""

        return DummyProcess()

    monkeypatch.setattr(
        "public_officer_pipeline.http_client.asyncio.create_subprocess_exec",
        fake_subprocess_exec,
    )

    client = _CurlClient(timeout=1.0, headers={}, follow_redirects=False)
    response = await client.get("https://example.com/list")

    assert response.text == "already decoded"
    assert response.headers["Content-encoding"] == "gzip"


@pytest.mark.asyncio
async def test_create_http_client_from_env_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    timeout = httpx.Timeout(3.0, connect=2.0)

    monkeypatch.setenv("PIPELINE_HTTP_BACKEND", "curl")
    curl_client = create_http_client(timeout=timeout, headers={}, follow_redirects=True)
    assert isinstance(curl_client, _CurlClient)

    monkeypatch.setenv("PIPELINE_HTTP_BACKEND", "httpx")
    httpx_client = create_http_client(timeout=timeout, headers={}, follow_redirects=True)
    assert isinstance(httpx_client, _HttpxClient)

    monkeypatch.setenv("PIPELINE_HTTP_BACKEND", "auto")
    auto_client = create_http_client(timeout=timeout, headers={}, follow_redirects=True)
    assert isinstance(auto_client, _AdaptiveHttpClient)


@pytest.mark.asyncio
async def test_curl_client_returns_request_error_on_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_subprocess_exec(*_args: object, **_kwargs: object):
        class DummyProcess:
            returncode = 7

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", b"boom"

        return DummyProcess()

    monkeypatch.setattr(
        "public_officer_pipeline.http_client.asyncio.create_subprocess_exec",
        fake_subprocess_exec,
    )

    client = _CurlClient(timeout=1.0, headers={}, follow_redirects=False)

    with pytest.raises(httpx.RequestError):
        await client.get("https://example.com")


@pytest.mark.asyncio
async def test_curl_client_uses_doh_url_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[str] = []

    async def fake_subprocess_exec(*args: object, **_kwargs: object):
        command = list(args)
        captured.extend(str(item) for item in command)
        _write_curl_files(args)

        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", b""

        return DummyProcess()

    monkeypatch.setattr(
        "public_officer_pipeline.http_client.asyncio.create_subprocess_exec",
        fake_subprocess_exec,
    )

    client = _CurlClient(
        timeout=1.0,
        headers={},
        follow_redirects=True,
        doh_url="https://1.1.1.1/dns-query",
    )
    response = await client.get("https://example.com")

    assert response.status_code == 200
    assert response.text == "ok"
    assert "--doh-url" in captured
    assert "https://1.1.1.1/dns-query" in captured


@pytest.mark.asyncio
async def test_curl_client_allows_per_request_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[str] = []

    async def fake_subprocess_exec(*args: object, **_kwargs: object):
        captured.extend(str(item) for item in args)
        _write_curl_files(args)

        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", b""

        return DummyProcess()

    monkeypatch.setattr(
        "public_officer_pipeline.http_client.asyncio.create_subprocess_exec",
        fake_subprocess_exec,
    )

    client = _CurlClient(timeout=1.0, headers={"User-Agent": "base"}, follow_redirects=True)
    response = await client.get(
        "https://example.com/file.pdf",
        headers={"Referer": "https://example.com/list"},
    )

    assert response.text == "ok"
    assert "User-Agent: base" in captured
    assert "Referer: https://example.com/list" in captured


@pytest.mark.asyncio
async def test_httpx_client_rejects_oversized_content_length() -> None:
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(
            200,
            headers={"Content-Length": "5"},
            content=b"12345",
        )
    )
    client = _HttpxClient(
        timeout=httpx.Timeout(1.0),
        headers={},
        follow_redirects=True,
        max_download_bytes=4,
        transport=transport,
    )

    try:
        with pytest.raises(guards.DocumentProcessingLimitError, match="Content-Length"):
            await client.get("https://example.com/file.pdf")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_httpx_client_rejects_oversized_streamed_body() -> None:
    class OversizedStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield b"12"
            yield b"345"

    transport = httpx.MockTransport(lambda _request: httpx.Response(200, stream=OversizedStream()))
    client = _HttpxClient(
        timeout=httpx.Timeout(1.0),
        headers={},
        follow_redirects=True,
        max_download_bytes=4,
        transport=transport,
    )

    try:
        with pytest.raises(guards.DocumentProcessingLimitError, match="body"):
            await client.get("https://example.com/file.pdf")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_curl_client_sets_max_filesize_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[str] = []

    async def fake_subprocess_exec(*args: object, **_kwargs: object):
        captured.extend(str(item) for item in args)
        _write_curl_files(args)

        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", b""

        return DummyProcess()

    monkeypatch.setattr(
        "public_officer_pipeline.http_client.asyncio.create_subprocess_exec",
        fake_subprocess_exec,
    )

    client = _CurlClient(
        timeout=1.0,
        headers={},
        follow_redirects=False,
        max_download_bytes=17,
    )
    await client.get("https://example.com/file.pdf")

    assert "--max-filesize" in captured
    assert captured[captured.index("--max-filesize") + 1] == "17"


@pytest.mark.asyncio
async def test_curl_client_can_disable_compressed_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[str] = []

    async def fake_subprocess_exec(*args: object, **_kwargs: object):
        captured.extend(str(item) for item in args)
        _write_curl_files(args)

        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", b""

        return DummyProcess()

    monkeypatch.setattr(
        "public_officer_pipeline.http_client.asyncio.create_subprocess_exec",
        fake_subprocess_exec,
    )

    client = _CurlClient(timeout=1.0, headers={}, follow_redirects=False, compressed=False)
    await client.get("https://example.com/file.pdf")

    assert "--compressed" not in captured


@pytest.mark.asyncio
async def test_adaptive_client_retries_decode_errors_with_identity_curl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[str] = []

    async def fake_primary_get(*_args: object, **_kwargs: object):
        raise httpx.DecodingError("incorrect header check")

    async def fake_subprocess_exec(*args: object, **_kwargs: object):
        captured.extend(str(item) for item in args)
        _write_curl_files(args, body_bytes="업무추진비".encode())

        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", b""

        return DummyProcess()

    monkeypatch.setattr(
        "public_officer_pipeline.http_client.asyncio.create_subprocess_exec",
        fake_subprocess_exec,
    )

    client = _AdaptiveHttpClient(
        timeout=httpx.Timeout(1.0),
        headers={"User-Agent": "base"},
        follow_redirects=False,
    )
    monkeypatch.setattr(client._primary, "get", fake_primary_get)

    try:
        response = await client.get("https://example.com/file.pdf")
    finally:
        await client.aclose()

    assert response.text == "업무추진비"
    assert "--compressed" not in captured
    assert "Accept-Encoding: identity" in captured


@pytest.mark.asyncio
async def test_adaptive_client_retries_protocol_errors_with_curl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[str] = []

    async def fake_primary_get(*_args: object, **_kwargs: object):
        request = httpx.Request("GET", "https://example.com/list")
        raise httpx.RemoteProtocolError("continuation line at start of headers", request=request)

    async def fake_subprocess_exec(*args: object, **_kwargs: object):
        captured.extend(str(item) for item in args)
        _write_curl_files(args, body_bytes="업무추진비".encode())

        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", b""

        return DummyProcess()

    monkeypatch.setattr(
        "public_officer_pipeline.http_client.asyncio.create_subprocess_exec",
        fake_subprocess_exec,
    )

    client = _AdaptiveHttpClient(
        timeout=httpx.Timeout(1.0),
        headers={"User-Agent": "base"},
        follow_redirects=False,
    )
    monkeypatch.setattr(client._primary, "get", fake_primary_get)

    try:
        response = await client.get("https://example.com/list")
    finally:
        await client.aclose()

    assert response.text == "업무추진비"
    assert "--compressed" in captured
    assert "Accept-Encoding: identity" not in captured


@pytest.mark.asyncio
async def test_curl_client_rejects_oversized_parsed_body(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_subprocess_exec(*_args: object, **_kwargs: object):
        _write_curl_files(_args, body_bytes=b"12345")

        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", b""

        return DummyProcess()

    monkeypatch.setattr(
        "public_officer_pipeline.http_client.asyncio.create_subprocess_exec",
        fake_subprocess_exec,
    )

    client = _CurlClient(
        timeout=1.0,
        headers={},
        follow_redirects=False,
        max_download_bytes=4,
    )

    with pytest.raises(guards.DocumentProcessingLimitError, match="body"):
        await client.get("https://example.com/file.pdf")
