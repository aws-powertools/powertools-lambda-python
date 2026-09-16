import pytest

from aws_lambda_powertools.utilities.auth import JWTVerifier
from aws_lambda_powertools.utilities.auth.exceptions import InvalidTokenError
from aws_lambda_powertools.utilities.auth.testing import mock_claims


def test_mock_claims_is_scoped_and_restores_real_verification(jwks):
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
    )

    with mock_claims(verifier, {"sub": "test-user", "scope": "orders:read"}):
        assert verifier.verify("not-a-real-token") == {"sub": "test-user", "scope": "orders:read"}
    with pytest.raises(InvalidTokenError):
        verifier.verify("not-a-real-token")


def test_mock_claims_returns_independent_snapshots_and_avoids_network(http):
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
    )
    claims = {"sub": "test-user", "roles": ["reader"]}

    with mock_claims(verifier, claims):
        first = verifier.verify("token")
        first["roles"].append("admin")
        assert verifier.verify("token") == {"sub": "test-user", "roles": ["reader"]}
    assert http.requests == []
