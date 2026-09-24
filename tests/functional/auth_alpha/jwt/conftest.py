import time
import weakref

import jwt
import pytest
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


@pytest.fixture(autouse=True)
def isolated_jwks_caches(monkeypatch):
    # Each test's fake provider owns its cache, independent of retained tracebacks.
    monkeypatch.setattr(jwks_module, "_caches", weakref.WeakValueDictionary())
