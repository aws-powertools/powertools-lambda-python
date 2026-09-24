import base64
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs

import pytest

from aws_lambda_powertools.utilities.auth_alpha import OAuth2Client
from aws_lambda_powertools.utilities.auth_alpha.oauth2.exceptions import DownstreamRequestError, TokenExchangeError

TOKEN_RESPONSE = {"access_token": "local-test-token", "token_type": "Bearer", "expires_in": 600}


def client(endpoint, **options):
    return OAuth2Client(
        token_url=endpoint.url + "/token",
        client_id="orders",
        client_secret="test-only-secret",
        scopes=["inventory:read"],
        **options,
    )


@pytest.mark.parametrize("chunked", [False, True])
def test_token_exchange_and_authenticated_request_over_trusted_tls(https_server, chunked):
    https_server.serve("/token", TOKEN_RESPONSE, chunked=chunked)
    https_server.serve("/inventory", {"items": [123]}, chunked=chunked)
    subject = client(https_server)

    response = subject.request("GET", https_server.url + "/inventory")

    assert response.status == 200
    assert response.json() == {"items": [123]}
    assert subject.auth_headers() == {"Authorization": "Bearer local-test-token"}
    exchange, resource = https_server.requests
    assert exchange[:2] == ("POST", "/token")
    assert base64.b64decode(exchange[2]["Authorization"].removeprefix("Basic ")).decode() == "orders:test-only-secret"
    assert parse_qs(exchange[3].decode()) == {"grant_type": ["client_credentials"], "scope": ["inventory:read"]}
    assert resource[2]["Authorization"] == "Bearer local-test-token"
    assert "test-only-secret" not in str(resource)


def test_downstream_redirects_are_returned_without_forwarding_bearer_tokens(https_server):
    https_server.serve("/token", TOKEN_RESPONSE)
    https_server.serve("/inventory", {}, status=307, headers={"Location": https_server.url + "/other"})
    https_server.serve("/other", {})

    response = client(https_server).request("GET", https_server.url + "/inventory")

    assert response.status == 307
    assert [request[1] for request in https_server.requests] == ["/token", "/inventory"]


def test_downstream_failures_are_not_retried(https_server):
    https_server.serve("/token", TOKEN_RESPONSE)
    https_server.serve("/inventory", {}, status=503)
    assert client(https_server).request("POST", https_server.url + "/inventory").status == 503
    assert [request[1] for request in https_server.requests] == ["/token", "/inventory"]


def test_downstream_timeout_has_a_separate_budget_and_a_sanitized_error(https_server):
    https_server.serve("/token", TOKEN_RESPONSE)
    https_server.serve("/inventory", {"items": []}, stall=True)
    subject = client(https_server, timeout_seconds=3)
    started = time.monotonic()

    with pytest.raises(DownstreamRequestError) as error:
        subject.request("GET", https_server.url + "/inventory", timeout=0.2)

    assert time.monotonic() - started < 1
    assert error.value.__context__ is None
    assert [request[1] for request in https_server.requests] == ["/token", "/inventory"]


def test_untrusted_tls_never_sends_client_credentials(https_server, monkeypatch):
    monkeypatch.delenv("SSL_CERT_FILE")
    https_server.serve("/token", TOKEN_RESPONSE)
    subject = client(https_server, timeout_seconds=0.15)

    with pytest.raises(TokenExchangeError) as error:
        subject.auth_headers()
    assert error.value.__context__ is None
    assert https_server.requests == []


@pytest.mark.parametrize("failure", ["oversized", "redirect", "stall", "trickle"])
def test_exchange_failures_are_bounded_without_forwarding_credentials(https_server, failure):
    if failure == "oversized":
        https_server.serve("/token", b'{"padding":"' + b"x" * (1024 * 1024) + b'"}')
    elif failure == "redirect":
        https_server.serve("/token", {}, status=307, headers={"Location": https_server.url + "/redirected"})
        https_server.serve("/redirected", TOKEN_RESPONSE)
    else:
        https_server.serve(
            "/token",
            TOKEN_RESPONSE,
            stall=failure == "stall",
            interval=0.04 if failure == "trickle" else 0,
        )
    subject = client(https_server, timeout_seconds=0.2)
    started = time.monotonic()

    with pytest.raises(TokenExchangeError) as error:
        subject.auth_headers()
    assert time.monotonic() - started < 1
    assert error.value.__context__ is None
    assert [request[1] for request in https_server.requests] == ["/token"]


def test_slow_downstream_body_cannot_extend_the_timeout(https_server):
    https_server.serve("/token", TOKEN_RESPONSE)
    https_server.serve("/inventory", {"items": list(range(100))}, interval=0.04)
    subject = client(https_server)
    started = time.monotonic()

    with pytest.raises(DownstreamRequestError):
        subject.request("GET", https_server.url + "/inventory", timeout=0.2)
    assert time.monotonic() - started < 1
    assert [request[1] for request in https_server.requests] == ["/token", "/inventory"]


@pytest.fixture(params=["header", "chunk_size", "trailer"])
def slow_framing(request):
    return {f"{request.param}_interval": 0.04, "chunked": request.param != "header"}


def test_slow_token_framing_cannot_extend_the_acquisition_timeout(https_server, slow_framing):
    https_server.serve("/token", TOKEN_RESPONSE, **slow_framing)
    subject = client(https_server, timeout_seconds=0.2)
    started = time.monotonic()

    with pytest.raises(TokenExchangeError) as error:
        subject.auth_headers()

    assert time.monotonic() - started < 1
    assert error.value.retryable
    assert error.value.__context__ is None
    assert error.value.__cause__ is None
    assert [request[1] for request in https_server.requests] == ["/token"]

    https_server.serve("/token", TOKEN_RESPONSE)
    assert subject.auth_headers() == {"Authorization": "Bearer local-test-token"}
    assert [request[1] for request in https_server.requests] == ["/token", "/token"]


def test_slow_downstream_framing_cannot_extend_the_request_timeout(https_server, slow_framing):
    https_server.serve("/token", TOKEN_RESPONSE)
    https_server.serve("/inventory", {"items": [123]}, **slow_framing)
    subject = client(https_server)
    subject.auth_headers()
    started = time.monotonic()

    with pytest.raises(DownstreamRequestError) as error:
        subject.request("GET", https_server.url + "/inventory", timeout=0.2)

    assert time.monotonic() - started < 1
    assert not error.value.retryable
    assert error.value.__context__ is None
    assert error.value.__cause__ is None
    assert [request[1] for request in https_server.requests] == ["/token", "/inventory"]

    https_server.serve("/inventory", {"items": [123]})
    assert subject.request("GET", https_server.url + "/inventory").json() == {"items": [123]}
    assert [request[1] for request in https_server.requests] == ["/token", "/inventory", "/inventory"]


def test_concurrent_downstream_requests_keep_separate_deadlines(https_server):
    https_server.serve("/token", TOKEN_RESPONSE)
    https_server.serve("/inventory", {"items": [123]}, header_interval=0.01)
    subject = client(https_server)
    subject.auth_headers()
    ready = threading.Barrier(2)

    def request(timeout):
        ready.wait(timeout=2)
        return subject.request("GET", https_server.url + "/inventory", timeout=timeout)

    with ThreadPoolExecutor(max_workers=2) as executor:
        short = executor.submit(request, 0.15)
        long = executor.submit(request, 2)
        with pytest.raises(DownstreamRequestError):
            short.result(timeout=3)
        assert long.result(timeout=3).json() == {"items": [123]}

    assert [request[1] for request in https_server.requests] == ["/token", "/inventory", "/inventory"]


def test_body_reads_use_the_budget_remaining_after_headers(https_server):
    https_server.serve("/token", TOKEN_RESPONSE)
    # Header receipt consumes about 0.2s; the trailer must use what remains,
    # rather than starting another downstream timeout after the headers.
    https_server.serve(
        "/inventory",
        {"items": [123]},
        header_interval=0.005,
        chunked=True,
        trailer_interval=0.04,
    )
    subject = client(https_server)
    subject.auth_headers()
    started = time.monotonic()

    with pytest.raises(DownstreamRequestError):
        subject.request("GET", https_server.url + "/inventory", timeout=0.4)

    assert time.monotonic() - started < 0.6
    assert [request[1] for request in https_server.requests] == ["/token", "/inventory"]


@pytest.mark.parametrize("chunked", [False, True])
def test_downstream_gzip_response_remains_readable(https_server, chunked):
    import gzip

    https_server.serve("/token", TOKEN_RESPONSE)
    https_server.serve(
        "/inventory",
        gzip.compress(b'{"items":[123]}'),
        headers={"Content-Encoding": "gzip"},
        chunked=chunked,
    )
    subject = client(https_server)

    response = subject.request("GET", https_server.url + "/inventory")
    assert response.json() == {"items": [123]}
