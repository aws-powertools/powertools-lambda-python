import base64
import time
from urllib.parse import parse_qs

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from aws_lambda_powertools.utilities.auth import JWTVerifier, OAuth2Client
from aws_lambda_powertools.utilities.auth.exceptions import AuthError, JWKSFetchError, TokenExchangeError

TOKEN_RESPONSE = {"access_token": "local-test-token", "token_type": "Bearer", "expires_in": 600}


def client(endpoint, **options):
    return OAuth2Client(
        token_url=endpoint.url + "/token",
        client_id="orders",
        client_secret="test-only-secret",
        scopes=["inventory:read"],
        **options,
    )


def verifier(endpoint, **options):
    return JWTVerifier(issuer=endpoint.url, audience="orders", algorithms=["RS256"], **options)


def test_discovery_and_jwks_verify_a_real_signature_over_trusted_tls(https_server):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    https_server.serve(
        "/.well-known/openid-configuration",
        {
            "issuer": https_server.url,
            "jwks_uri": https_server.url + "/keys",
        },
    )
    https_server.serve("/keys", {"keys": [{**jwk, "kid": "test-key", "alg": "RS256", "use": "sig"}]})
    token = jwt.encode(
        {"iss": https_server.url, "aud": "orders", "exp": int(time.time()) + 600, "sub": "test-user"},
        key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )
    subject = verifier(https_server)
    subject.prefetch()
    assert subject.verify(token)["sub"] == "test-user"
    assert subject.verify(token)["sub"] == "test-user"
    assert [request[1] for request in https_server.requests] == ["/.well-known/openid-configuration", "/keys"]


def test_token_exchange_and_authenticated_request_over_trusted_tls(https_server):
    https_server.serve("/token", TOKEN_RESPONSE)
    https_server.serve("/inventory", {"items": [123]})
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


@pytest.mark.parametrize("operation", ["prefetch", "auth_headers"])
def test_untrusted_certificates_fail_closed_without_sending_credentials(https_server, monkeypatch, operation):
    monkeypatch.delenv("SSL_CERT_FILE")
    https_server.serve("/token", TOKEN_RESPONSE)
    https_server.serve("/keys", {"keys": []})
    if operation == "prefetch":
        subject = verifier(https_server, jwks_uri=https_server.url + "/keys")
        expected_error = JWKSFetchError
    else:
        subject = client(https_server, timeout_seconds=0.5)
        expected_error = TokenExchangeError
    with pytest.raises(expected_error) as error:
        getattr(subject, operation)()
    assert error.value.__context__ is None
    assert error.value.__cause__ is None
    assert https_server.requests == []


@pytest.mark.parametrize("endpoint", ["keys", "token"])
@pytest.mark.parametrize("failure", ["oversized", "redirect", "stall", "trickle"])
def test_auth_endpoint_failures_are_bounded_and_do_not_follow_redirects(https_server, endpoint, failure):
    payload = {"keys": []} if endpoint == "keys" else TOKEN_RESPONSE
    if failure == "oversized":
        https_server.serve("/" + endpoint, b'{"padding":"' + b"x" * (1024 * 1024) + b'"}')
    elif failure == "redirect":
        https_server.serve("/" + endpoint, {}, status=307, headers={"Location": https_server.url + "/redirected"})
        https_server.serve("/redirected", payload)
    else:
        https_server.serve(
            "/" + endpoint,
            payload,
            stall=failure == "stall",
            interval=0.04 if failure == "trickle" else 0,
        )
    if endpoint == "keys":
        subject = verifier(https_server, jwks_uri=https_server.url + "/keys", timeout_seconds=0.2)
        operation, expected_error = subject.prefetch, JWKSFetchError
    else:
        subject = client(https_server, timeout_seconds=0.2)
        operation, expected_error = subject.auth_headers, TokenExchangeError

    started = time.monotonic()
    with pytest.raises(expected_error) as error:
        operation()
    assert time.monotonic() - started < 1
    assert error.value.__context__ is None
    assert [request[1] for request in https_server.requests] == ["/" + endpoint]


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

    with pytest.raises(AuthError) as error:
        subject.request("GET", https_server.url + "/inventory", timeout=0.2)

    assert time.monotonic() - started < 1
    assert error.value.__context__ is None
    assert [request[1] for request in https_server.requests] == ["/token", "/inventory"]
