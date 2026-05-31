import httpx
import pytest

from public_officer_pipeline import document_guards as guards
from public_officer_pipeline.http_client import (
    _AdaptiveHttpClient,
    _CurlClient,
    _HttpxClient,
    _build_url_with_params,
    create_http_client,
)


def test_build_url_with_params_keeps_existing_query_values() -> None:
    assert (
        _build_url_with_params("https://example.com/search?year=2026", {"page": 3})
        == "https://example.com/search?year=2026&page=3"
    )


def test_curl_output_parser_prefers_last_http_response() -> None:
    client = _CurlClient(timeout=1.0, headers={}, follow_redirects=True)

    raw_output = (
        "HTTP/1.1 301 Moved\r\nLocation: /legacy\r\n\r\nignored\r\n"
        "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nfinal"
    ).encode("utf-8")

    status_code, body, headers = client._parse_curl_output(raw_output)

    assert status_code == 200
    assert body == b"final"
    assert headers == {"Content-Type": "text/plain"}


def test_curl_output_parser_preserves_binary_body_offsets() -> None:
    client = _CurlClient(timeout=1.0, headers={}, follow_redirects=True)

    binary_body = b"%PDF-1.4\n%\xff\xfe\xfa\n10 0 obj\n"
    raw_output = b"HTTP/1.1 200 OK\r\nContent-Type: application/pdf\r\n\r\n" + binary_body

    status_code, body, headers = client._parse_curl_output(raw_output)

    assert status_code == 200
    assert body == binary_body
    assert headers == {"Content-Type": "application/pdf"}


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

    async def fake_subprocess_exec(*args: object, **kwargs: object):
        command = list(args)
        captured.extend(str(item) for item in command)

        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                response = (
                    "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nok"
                ).encode("utf-8")
                return response, b""

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

    async def fake_subprocess_exec(*args: object, **kwargs: object):
        captured.extend(str(item) for item in args)

        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nok", b""

        return DummyProcess()

    monkeypatch.setattr(
        "public_officer_pipeline.http_client.asyncio.create_subprocess_exec",
        fake_subprocess_exec,
    )

    client = _CurlClient(timeout=1.0, headers={"User-Agent": "base"}, follow_redirects=True)
    response = await client.get("https://example.com/file.pdf", headers={"Referer": "https://example.com/list"})

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

    async def fake_subprocess_exec(*args: object, **kwargs: object):
        captured.extend(str(item) for item in args)

        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nok", b""

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
async def test_curl_client_rejects_oversized_parsed_body(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_subprocess_exec(*_args: object, **_kwargs: object):
        class DummyProcess:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n12345", b""

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
