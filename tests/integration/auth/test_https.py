import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from aws_lambda_powertools.utilities.auth import JWTVerifier
from aws_lambda_powertools.utilities.auth.exceptions import JWKSFetchError


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


def test_untrusted_certificates_fail_before_sending_a_request(https_server, monkeypatch):
    monkeypatch.delenv("SSL_CERT_FILE")
    https_server.serve("/keys", {"keys": []})
    subject = verifier(https_server, jwks_uri=https_server.url + "/keys")
    with pytest.raises(JWKSFetchError) as error:
        subject.prefetch()
    assert error.value.__context__ is None
    assert error.value.__cause__ is None
    assert https_server.requests == []


@pytest.mark.parametrize("failure", ["oversized", "redirect", "stall", "trickle"])
def test_key_endpoint_failures_are_bounded_and_do_not_follow_redirects(https_server, failure):
    payload = {"keys": []}
    if failure == "oversized":
        https_server.serve("/keys", b'{"padding":"' + b"x" * (1024 * 1024) + b'"}')
    elif failure == "redirect":
        https_server.serve("/keys", {}, status=307, headers={"Location": https_server.url + "/redirected"})
        https_server.serve("/redirected", payload)
    else:
        https_server.serve(
            "/keys",
            payload,
            stall=failure == "stall",
            interval=0.04 if failure == "trickle" else 0,
        )
    subject = verifier(https_server, jwks_uri=https_server.url + "/keys", timeout_seconds=0.2)

    started = time.monotonic()
    with pytest.raises(JWKSFetchError) as error:
        subject.prefetch()
    assert time.monotonic() - started < 1
    assert error.value.__context__ is None
    assert [request[1] for request in https_server.requests] == ["/keys"]
