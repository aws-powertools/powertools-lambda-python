import base64
import threading
import time
import traceback
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs

import pytest

from aws_lambda_powertools.utilities.auth_alpha import OAuth2Client
from aws_lambda_powertools.utilities.auth_alpha.oauth2.exceptions import TokenExchangeError

TOKEN_URL = "https://idp.example.com/oauth/token"


def client(**options):
    config = {
        "token_url": TOKEN_URL,
        "client_id": "orders-client",
        "client_secret": "test-client-secret",
        "scopes": ["orders:read"],
    }
    return OAuth2Client(**{**config, **options})


def test_client_credentials_exchange_selects_resource_and_caches_token(http):
    http.serve(
        TOKEN_URL,
        {"access_token": "opaque-access-token", "token_type": "Bearer", "expires_in": 3600},
        method="POST",
    )
    subject = client(audience="https://api.example.com")

    assert subject.auth_headers() == {"Authorization": "Bearer opaque-access-token"}
    assert subject.auth_headers() == {"Authorization": "Bearer opaque-access-token"}
    assert len(http.requests) == 1
    method, url, request = http.requests[0]
    assert method == "POST"
    assert url == TOKEN_URL
    assert parse_qs(request["body"].decode()) == {
        "grant_type": ["client_credentials"],
        "scope": ["orders:read"],
        "audience": ["https://api.example.com"],
    }
    assert request["headers"]["Content-Type"] == "application/x-www-form-urlencoded"


def test_basic_auth_encodes_each_credential_before_base64(http):
    http.serve(TOKEN_URL, {"access_token": "token", "token_type": "bearer", "expires_in": 3600}, method="POST")
    subject = client(client_id="client:id", client_secret="secret:value with space")
    subject.auth_headers()
    request = http.requests[0][2]
    encoded = request["headers"]["Authorization"].removeprefix("Basic ")

    assert base64.b64decode(encoded).decode() == "client%3Aid:secret%3Avalue+with+space"
    assert "client_secret" not in parse_qs(request["body"].decode())


def test_token_is_reacquired_before_expiry_using_the_current_secret(http, clock):
    secret = ["initial-secret"]
    observed = []

    def load_secret():
        observed.append(secret[0])
        return secret[0]

    http.serve(TOKEN_URL, {"access_token": "first", "token_type": "Bearer", "expires_in": 100}, method="POST")
    subject = client(client_secret=load_secret)
    assert subject.auth_headers()["Authorization"] == "Bearer first"
    clock.advance(69)
    assert subject.auth_headers()["Authorization"] == "Bearer first"
    assert observed == ["initial-secret"]
    secret[0] = "rotated-secret"
    http.serve(TOKEN_URL, {"access_token": "second", "token_type": "Bearer", "expires_in": 100}, method="POST")
    clock.advance(1)

    assert subject.auth_headers()["Authorization"] == "Bearer second"
    assert observed == ["initial-secret", "rotated-secret"]


@pytest.mark.parametrize("lifetime", [1, 30, None])
def test_short_lived_tokens_and_tokens_without_lifetimes_are_not_cached(http, lifetime):
    payload = {"access_token": "first", "token_type": "Bearer"}
    if lifetime is not None:
        payload["expires_in"] = lifetime
    http.serve(TOKEN_URL, payload, method="POST")
    subject = client()
    assert subject.auth_headers()["Authorization"] == "Bearer first"
    http.serve(TOKEN_URL, {**payload, "access_token": "second"}, method="POST")

    assert subject.auth_headers()["Authorization"] == "Bearer second"
    assert len(http.requests) == 2


@pytest.mark.parametrize(
    "override",
    [
        {"access_token": ""},
        {"access_token": None},
        {"access_token": "token\r\ninjected"},
        {"token_type": "DPoP"},
        {"token_type": None},
        {"expires_in": "3600"},
        {"expires_in": 0},
        {"expires_in": -1},
        {"expires_in": True},
        {"expires_in": None},
        {"expires_in": float("inf")},
    ],
)
def test_invalid_token_responses_are_rejected_without_retry(http, override):
    payload = {"access_token": "token", "token_type": "Bearer", "expires_in": 3600, **override}
    http.serve(TOKEN_URL, payload, method="POST")

    subject = client()
    with pytest.raises(TokenExchangeError):
        subject.auth_headers()
    assert len(http.requests) == 1


def test_resources_have_separate_token_caches_and_request_parameters(http):
    http.responses[("POST", TOKEN_URL)] = deque(
        [
            (200, {"access_token": "orders-token", "token_type": "Bearer", "expires_in": 3600}),
            (200, {"access_token": "inventory-token", "token_type": "Bearer", "expires_in": 3600}),
        ],
    )
    orders = client(audience="https://orders.example.com")
    inventory = client(resource="https://inventory.example.com")

    assert orders.auth_headers()["Authorization"] == "Bearer orders-token"
    assert inventory.auth_headers()["Authorization"] == "Bearer inventory-token"
    assert orders.auth_headers()["Authorization"] == "Bearer orders-token"
    assert len(http.requests) == 2
    assert parse_qs(http.requests[0][2]["body"].decode())["audience"] == ["https://orders.example.com"]
    assert parse_qs(http.requests[1][2]["body"].decode())["resource"] == ["https://inventory.example.com"]


@pytest.mark.parametrize("status", [400, 401, 403])
def test_permanent_exchange_errors_are_not_retried(http, status):
    http.serve(
        TOKEN_URL,
        {"error": "invalid_client", "error_description": "private details"},
        status=status,
        method="POST",
    )

    subject = client()
    with pytest.raises(TokenExchangeError):
        subject.auth_headers()
    assert len(http.requests) == 1


def test_transient_exchange_errors_have_at_most_two_retries(http, clock, monkeypatch):
    http.serve(TOKEN_URL, b"temporarily unavailable", status=503, method="POST")
    monkeypatch.setattr(time, "sleep", clock.advance)
    secrets = []

    def load_secret():
        secrets.append("secret")
        return secrets[-1]

    subject = client(client_secret=load_secret)
    with pytest.raises(TokenExchangeError):
        subject.auth_headers()
    assert len(http.requests) == 3
    assert len(secrets) == 3


def test_transient_exchange_can_recover_within_the_same_budget(http, clock, monkeypatch):
    http.responses[("POST", TOKEN_URL)] = deque(
        [(429, {}), (200, {"access_token": "recovered", "token_type": "Bearer", "expires_in": 100})],
    )
    monkeypatch.setattr(time, "sleep", clock.advance)

    assert client().auth_headers() == {"Authorization": "Bearer recovered"}
    assert len(http.requests) == 2


def test_exchange_cannot_accept_a_response_after_its_deadline(http, clock):
    def slow_endpoint():
        clock.advance(4)
        return {"access_token": "too-late", "token_type": "Bearer", "expires_in": 3600}

    http.serve(TOKEN_URL, slow_endpoint, method="POST")
    subject = client(timeout_seconds=3)
    with pytest.raises(TokenExchangeError):
        subject.auth_headers()
    assert len(http.requests) == 1


def test_exchange_cannot_return_a_token_that_expired_during_the_request(http, clock):
    def slow_endpoint():
        clock.advance(2)
        return {"access_token": "already-expired", "token_type": "Bearer", "expires_in": 1}

    http.serve(TOKEN_URL, slow_endpoint, method="POST")
    subject = client()
    with pytest.raises(TokenExchangeError):
        subject.auth_headers()


def test_concurrent_requests_share_one_token_exchange(http):
    entered = threading.Event()
    release = threading.Event()

    def exchange():
        entered.set()
        assert release.wait(2)
        return {"access_token": "shared-token", "token_type": "Bearer", "expires_in": 100}

    http.serve(TOKEN_URL, exchange, method="POST")
    subject = client()
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = [executor.submit(subject.auth_headers) for _ in range(8)]
        assert entered.wait(2)
        release.set()
        assert all(result.result(timeout=2) == {"Authorization": "Bearer shared-token"} for result in results)
    assert len(http.requests) == 1


@pytest.mark.parametrize("status", [200, 401], ids=["success", "failure"])
def test_concurrent_callers_share_reacquisition_at_the_refresh_boundary(http, clock, monkeypatch, status):
    http.serve(TOKEN_URL, {"access_token": "old", "token_type": "Bearer", "expires_in": 100}, method="POST")
    subject = client()
    assert subject.auth_headers() == {"Authorization": "Bearer old"}
    clock.advance(69)
    assert subject.auth_headers() == {"Authorization": "Bearer old"}
    assert len(http.requests) == 1
    clock.advance(1)  # The old token is still valid, with exactly 30 seconds remaining.

    entered = threading.Event()
    release = threading.Event()
    joined = threading.Event()

    def exchange():
        entered.set()
        assert release.wait(5)
        if status == 200:
            return {"access_token": "replacement", "token_type": "Bearer", "expires_in": 100}
        return {"error": "invalid_client"}

    http.serve(TOKEN_URL, exchange, status=status, method="POST")
    with ThreadPoolExecutor(max_workers=3) as executor:
        owner = executor.submit(subject.auth_headers)
        waiters = []
        try:
            assert entered.wait(5)
            flight = subject._flight
            assert flight is not None
            wait = flight.done.wait

            def observe_wait(timeout):
                joined.set()
                return wait(timeout)

            monkeypatch.setattr(flight.done, "wait", observe_wait)
            for _ in range(2):
                joined.clear()
                waiters.append(executor.submit(subject.auth_headers))
                assert joined.wait(5)
            assert len(http.requests) == 2
            assert not owner.done()
            assert all(not waiter.done() for waiter in waiters)
        finally:
            release.set()

        for result in (owner, *waiters):
            if status == 200:
                assert result.result(timeout=5) == {"Authorization": "Bearer replacement"}
            else:
                with pytest.raises(TokenExchangeError):
                    result.result(timeout=5)
    assert len(http.requests) == 2

    if status == 200:
        assert subject.auth_headers() == {"Authorization": "Bearer replacement"}
        assert len(http.requests) == 2
    else:
        # A later caller must also exchange again instead of using the still-valid old token.
        with pytest.raises(TokenExchangeError):
            subject.auth_headers()
        assert len(http.requests) == 3


def test_secret_loader_errors_and_representations_are_redacted(http):
    def load_secret():
        raise RuntimeError("sensitive-loader-data")

    subject = client(client_secret=load_secret)
    with pytest.raises(TokenExchangeError) as error:
        subject.auth_headers()
    assert "sensitive-loader-data" not in "".join(traceback.format_exception(error.value))
    assert repr(subject) == "<OAuth2Client>"


@pytest.mark.parametrize(
    "options",
    [
        {"audience": "one", "resource": "two"},
        {"audience": " "},
        {"resource": ""},
        {"resource": 42},
        {"token_url": "http://idp.example.com/token"},
        {"token_url": "https://user:secret@idp.example.com/token"},
        {"client_id": ""},
        {"client_secret": ""},
        {"timeout_seconds": 0},
        {"timeout_seconds": float("inf")},
        {"scopes": ["scope\ninjection"]},
    ],
)
def test_invalid_client_configuration_is_rejected(options):
    with pytest.raises(ValueError):
        client(**options)


def test_request_attaches_resource_token_without_forwarding_client_credentials(http):
    http.serve(TOKEN_URL, {"access_token": "resource-token", "token_type": "Bearer", "expires_in": 100}, method="POST")
    http.serve("https://api.example.com/orders", {"orders": [123]})
    subject = client(audience="https://api.example.com")

    response = subject.request(
        "GET",
        "https://api.example.com/orders",
        headers={"Accept": "application/json"},
        timeout=5,
    )

    assert response.json() == {"orders": [123]}
    request = http.requests[-1][2]
    assert request["headers"] == {"Accept": "application/json", "Authorization": "Bearer resource-token"}
    assert request["redirect"] is False
    assert request["retries"] is False
    assert "test-client-secret" not in repr(subject)
    assert "resource-token" not in repr(subject)


@pytest.mark.parametrize(
    "url,options",
    [
        ("http://api.example.com/orders", {}),
        ("https://api.example.com/orders", {"headers": {"authorization": "other-token"}}),
        ("https://api.example.com/orders", {"redirect": True}),
        ("https://api.example.com/orders", {"retries": 3}),
        ("https://api.example.com/orders", {"timeout": 0}),
        ("https://api.example.com/orders", {"headers": [("Accept", "application/json")]}),
    ],
)
def test_request_rejects_unsafe_overrides_before_acquiring_credentials(http, url, options):
    subject = client()
    with pytest.raises(ValueError):
        subject.request("GET", url, **options)
    assert http.requests == []


def test_request_does_not_follow_redirects_or_retry_downstream_failures(http):
    http.serve(TOKEN_URL, {"access_token": "token", "token_type": "Bearer", "expires_in": 100}, method="POST")
    http.serve("https://api.example.com/orders", {}, status=302)
    subject = client()

    assert subject.request("GET", "https://api.example.com/orders").status == 302
    http.serve("https://api.example.com/orders", {}, status=503)
    assert subject.request("GET", "https://api.example.com/orders").status == 503
    assert len(http.requests) == 3


@pytest.mark.parametrize("method", [None, "", "GET /", "GET\r\nInjected"])
def test_invalid_http_methods_are_rejected_before_loading_credentials(http, method):
    calls = []

    def load_secret():
        calls.append(True)
        return "test-secret"

    subject = client(client_secret=load_secret)
    with pytest.raises(ValueError, match="HTTP method"):
        subject.request(method, "https://api.example.com/orders")
    assert calls == []
    assert http.requests == []


@pytest.mark.parametrize("secret", [None, "", 42])
def test_invalid_secret_loader_results_are_rejected_before_sending_credentials(http, secret):
    subject = client(client_secret=lambda: secret)
    with pytest.raises(TokenExchangeError) as error:
        subject.auth_headers()
    assert error.value.__context__ is None
    assert http.requests == []


def test_retry_stops_when_the_backoff_exceeds_the_remaining_budget(http, clock, monkeypatch):
    sleeps = []
    monkeypatch.setattr(time, "sleep", sleeps.append)
    http.serve(TOKEN_URL, {}, status=503, method="POST")

    subject = client(timeout_seconds=0.05)
    with pytest.raises(TokenExchangeError):
        subject.auth_headers()
    assert sleeps == []
    assert len(http.requests) == 1


def test_waiting_callers_share_a_failed_exchange_and_can_recover(http, monkeypatch):
    entered = threading.Event()
    release = threading.Event()
    joined = threading.Event()

    def exchange():
        entered.set()
        assert release.wait(5)
        return {"error": "invalid_client"}

    http.serve(TOKEN_URL, exchange, status=401, method="POST")
    subject = client()
    with ThreadPoolExecutor(max_workers=2) as executor:
        owner = executor.submit(subject.auth_headers)
        try:
            assert entered.wait(5)
            flight = subject._flight
            assert flight is not None
            wait = flight.done.wait

            def observe_wait(timeout):
                joined.set()
                return wait(timeout)

            # Keep the real Event; observe it so the provider is released only
            # after the second caller has joined the active exchange.
            monkeypatch.setattr(flight.done, "wait", observe_wait)
            waiter = executor.submit(subject.auth_headers)
            assert joined.wait(5)
        finally:
            release.set()
        for result in (owner, waiter):
            with pytest.raises(TokenExchangeError) as error:
                result.result(timeout=5)
            assert error.value.__context__ is None
    assert len(http.requests) == 1

    http.serve(TOKEN_URL, {"access_token": "recovered", "token_type": "Bearer", "expires_in": 100}, method="POST")
    assert subject.auth_headers() == {"Authorization": "Bearer recovered"}
    assert len(http.requests) == 2


def test_waiting_callers_timeout_without_returning_the_late_token(http):
    entered = threading.Event()
    release = threading.Event()

    def exchange():
        entered.set()
        assert release.wait(5)
        return {"access_token": "too-late", "token_type": "Bearer", "expires_in": 100}

    http.serve(TOKEN_URL, exchange, method="POST")
    subject = client(timeout_seconds=0.1)
    with ThreadPoolExecutor(max_workers=1) as executor:
        owner = executor.submit(subject.auth_headers)
        try:
            assert entered.wait(5)
            with pytest.raises(TokenExchangeError):
                subject.auth_headers()
            assert not owner.done()
            assert len(http.requests) == 1
        finally:
            release.set()
        with pytest.raises(TokenExchangeError):
            owner.result(timeout=5)

    http.serve(TOKEN_URL, {"access_token": "recovered", "token_type": "Bearer", "expires_in": 100}, method="POST")
    assert subject.auth_headers() == {"Authorization": "Bearer recovered"}
    assert len(http.requests) == 2


def test_configuration_and_returned_headers_do_not_mutate_the_token_cache(http):
    scopes = ["orders:read"]
    subject = client(scopes=scopes)
    scopes.append("orders:write")
    http.serve(TOKEN_URL, {"access_token": "token", "token_type": "Bearer", "expires_in": 100}, method="POST")

    headers = subject.auth_headers()
    headers["Authorization"] = "Bearer replacement"
    assert subject.auth_headers() == {"Authorization": "Bearer token"}
    assert parse_qs(http.requests[0][2]["body"].decode())["scope"] == ["orders:read"]
    assert len(http.requests) == 1


def test_unselected_resource_and_scopes_are_not_added_to_the_exchange(http):
    subject = client(scopes=[])
    http.serve(TOKEN_URL, {"access_token": "token", "token_type": "Bearer", "expires_in": 100}, method="POST")

    subject.auth_headers()
    assert parse_qs(http.requests[0][2]["body"].decode()) == {"grant_type": ["client_credentials"]}


@pytest.mark.parametrize("lifetime", [1, 30, None])
def test_concurrent_callers_share_an_uncacheable_token(http, monkeypatch, lifetime):
    entered = threading.Event()
    release = threading.Event()
    joined = threading.Event()
    payload = {"access_token": "shared", "token_type": "Bearer"}
    if lifetime is not None:
        payload["expires_in"] = lifetime

    def exchange():
        entered.set()
        assert release.wait(5)
        return payload

    subject = client()
    http.serve(TOKEN_URL, exchange, method="POST")
    with ThreadPoolExecutor(max_workers=2) as executor:
        owner = executor.submit(subject.auth_headers)
        try:
            assert entered.wait(5)
            flight = subject._flight
            assert flight is not None
            wait = flight.done.wait

            def observe_wait(timeout):
                joined.set()
                return wait(timeout)

            monkeypatch.setattr(flight.done, "wait", observe_wait)
            waiter = executor.submit(subject.auth_headers)
            assert joined.wait(5)
        finally:
            release.set()
        assert owner.result(timeout=5) == {"Authorization": "Bearer shared"}
        assert waiter.result(timeout=5) == {"Authorization": "Bearer shared"}
    assert len(http.requests) == 1
    subject.auth_headers()
    assert len(http.requests) == 2


def test_invalid_unicode_from_a_secret_loader_is_sanitized(http):
    subject = client(client_secret=lambda: "private-secret-\ud800")
    with pytest.raises(TokenExchangeError) as error:
        subject.auth_headers()
    assert error.value.__context__ is None
    assert "private-secret" not in "".join(traceback.format_exception(error.value))
    assert http.requests == []


@pytest.mark.parametrize("field", ["client_id", "audience", "resource"])
def test_invalid_configuration_encoding_is_rejected(field):
    options = {field: "\ud800"}
    with pytest.raises(ValueError, match="UTF-8"):
        client(**options)


@pytest.mark.parametrize(
    "resource",
    [
        "inventory",
        "/inventory",
        "//inventory.example.com",
        "https://inventory.example.com/#fragment",
        "https://inventory.example.com/#",
        "urn:example:inventory#fragment",
        " https://inventory.example.com",
        "https://inventory.example.com/\nstock",
        "https://inventory.example.com/\x00stock",
        "https://inventory.example.com/stock item",
        "https://inventory.example.com/%invalid",
        "https://[invalid",
    ],
)
def test_resource_must_be_an_absolute_uri_without_a_fragment(resource):
    with pytest.raises(ValueError, match="absolute URI without a fragment"):
        client(resource=resource)


@pytest.mark.parametrize(
    "selection",
    [
        {"resource": "urn:example:inventory"},
        {"resource": "https://inventory.example.com/stock?region=eu&category=%23parts"},
        {"resource": "http://inventory.example.com"},
        {"audience": "inventory"},
    ],
)
def test_valid_resource_identifiers_and_provider_audiences_are_preserved(http, selection):
    http.serve(TOKEN_URL, {"access_token": "token", "token_type": "Bearer", "expires_in": 100}, method="POST")
    subject = client(**selection)

    subject.auth_headers()

    name, value = next(iter(selection.items()))
    fields = parse_qs(http.requests[0][2]["body"].decode())
    assert fields[name] == [value]
    other = "audience" if name == "resource" else "resource"
    assert other not in fields


def test_secret_lookup_does_not_expire_a_new_short_lived_token(http, clock):
    def load_secret():
        clock.advance(2)
        return "test-secret"

    http.serve(TOKEN_URL, {"access_token": "fresh", "token_type": "Bearer", "expires_in": 1}, method="POST")
    subject = client(client_secret=load_secret, timeout_seconds=3)

    assert subject.auth_headers() == {"Authorization": "Bearer fresh"}
    assert subject.auth_headers() == {"Authorization": "Bearer fresh"}
    assert len(http.requests) == 2


def test_secret_lookup_does_not_move_the_cached_tokens_refresh_boundary(http, clock):
    def load_secret():
        clock.advance(2)
        return "test-secret"

    http.serve(TOKEN_URL, {"access_token": "first", "token_type": "Bearer", "expires_in": 100}, method="POST")
    subject = client(client_secret=load_secret)
    assert subject.auth_headers() == {"Authorization": "Bearer first"}
    clock.advance(69)
    assert subject.auth_headers() == {"Authorization": "Bearer first"}
    assert len(http.requests) == 1

    http.serve(TOKEN_URL, {"access_token": "second", "token_type": "Bearer", "expires_in": 100}, method="POST")
    clock.advance(1)
    assert subject.auth_headers() == {"Authorization": "Bearer second"}
    assert len(http.requests) == 2


def test_secret_lookup_still_consumes_the_acquisition_budget(http, clock):
    def load_secret():
        clock.advance(4)
        return "test-secret"

    subject = client(client_secret=load_secret, timeout_seconds=3)
    with pytest.raises(TokenExchangeError) as error:
        subject.auth_headers()

    assert error.value.retryable
    assert http.requests == []


@pytest.mark.parametrize(
    "name",
    [
        "Authorization",
        "aUtHoRiZaTiOn",
        "Authorization ",
        "Authorization\t",
        " Authorization",
        "",
        ":",
        "X:Trace",
        "X Trace",
        "X\tTrace",
        "X/Trace",
        "X(Trace)",
        "X\x00Trace",
        "X\x7fTrace",
        "X-Ünicode",
        "X-Trace\r\nInjected",
    ],
)
def test_invalid_header_names_are_rejected_before_token_acquisition(http, name):
    secrets = []

    def load_secret():
        secrets.append("test-secret")
        return secrets[-1]

    http.serve(TOKEN_URL, {"access_token": "token", "token_type": "Bearer", "expires_in": 100}, method="POST")
    http.serve("https://api.example.com/orders", {"orders": []})
    subject = client(client_secret=load_secret)

    with pytest.raises(ValueError, match="Request headers"):
        subject.request("GET", "https://api.example.com/orders", headers={name: "test-value"})

    assert secrets == []
    assert http.requests == []


def test_http_token_punctuation_is_allowed_in_header_names(http):
    http.serve(TOKEN_URL, {"access_token": "token", "token_type": "Bearer", "expires_in": 100}, method="POST")
    http.serve("https://api.example.com/orders", {"orders": []})
    subject = client()
    headers = {"X-Trace!#$%&'*+.^_`|~09": "trace-id"}

    response = subject.request("GET", "https://api.example.com/orders", headers=headers)

    assert response.status == 200
    assert http.requests[-1][2]["headers"] == {**headers, "Authorization": "Bearer token"}
