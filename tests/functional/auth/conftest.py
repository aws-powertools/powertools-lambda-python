import io
import json
import time
from collections import deque

import jwt
import pytest
import urllib3
from cryptography.hazmat.primitives.asymmetric import rsa


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
    def issue(payload=None, *, key=None, kid="key-1", algorithm="RS256"):
        return jwt.encode(
            claims if payload is None else payload,
            signing_key if key is None else key,
            algorithm=algorithm,
            headers={"kid": kid},
        )

    return issue


class FakeHTTP:
    """In-memory token and JWKS endpoints at the HTTP transport boundary."""

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
