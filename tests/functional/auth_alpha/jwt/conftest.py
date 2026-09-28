import io
import json
import time
import weakref
from collections import deque

import jwt
import pytest
import urllib3
from cryptography.hazmat.primitives.asymmetric import rsa

from aws_lambda_powertools.utilities.auth_alpha.jwt._internal import jwks as jwks_module


@pytest.fixture(scope="session")
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def jwks(signing_key):
    key = jwt.algorithms.RSAAlgorithm.to_jwk(signing_key.public_key(), as_dict=True)
    return {"keys": [{**key, "kid": "key-1", "use": "sig", "alg": "RS256"}]}


@pytest.fixture
def claims():
    return {
        "iss": "https://idp.example.com/",
        "aud": "https://api.example.com",
        "exp": int(time.time()) + 600,
        "sub": "user-123",
        "scope": "orders:read",
    }


@pytest.fixture
def issue_token(signing_key, claims):
    def issue(payload=None, *, key=None, kid="key-1", algorithm="RS256", headers=None):
        return jwt.encode(
            claims if payload is None else payload,
            signing_key if key is None else key,
            algorithm=algorithm,
            headers={"kid": kid, **(headers or {})},
        )

    return issue


class FakeHTTP:
    """In-memory JWKS endpoints at the HTTP transport boundary."""

    def __init__(self):
        self.responses = {}
        self.requests = []

    def serve(self, url, body, *, status=200, method="GET"):
        self.responses[(method, url)] = deque([(status, body)])

    def request(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))
        responses = self.responses[(method, url)]
        status, body = responses[0] if len(responses) == 1 else responses.popleft()
        if callable(body):
            body = body()
        if isinstance(body, Exception):
            raise body
        payload = body if isinstance(body, bytes) else json.dumps(body).encode()
        return urllib3.HTTPResponse(
            body=io.BytesIO(payload),
            headers={"content-type": "application/json"},
            status=status,
            preload_content=False,
        )


@pytest.fixture
def http(monkeypatch):
    # Each fake provider belongs to one test. Error tracebacks can keep a
    # previous verifier alive; retain sharing only within the current test.
    monkeypatch.setattr(jwks_module, "_caches", weakref.WeakValueDictionary())
    transport = FakeHTTP()
    monkeypatch.setattr(urllib3, "PoolManager", lambda **kwargs: transport)
    return transport


@pytest.fixture
def clock(monkeypatch):
    class Clock:
        now = 1000.0

        def __call__(self):
            return self.now

        def advance(self, seconds):
            self.now += seconds

    clock = Clock()
    monkeypatch.setattr(time, "monotonic", clock)
    return clock
