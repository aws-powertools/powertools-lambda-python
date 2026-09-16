import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from aws_lambda_powertools.utilities.auth import JWTVerifier
from aws_lambda_powertools.utilities.auth.exceptions import InvalidClaimsError, InvalidSignatureError, InvalidTokenError


def test_cognito_checks_app_client_and_resource_separately(jwks, claims, issue_token):
    verifier = JWTVerifier.cognito(
        user_pool_id="us-east-1_pool",
        client_id="desktop-client",
        audience="https://api.example.com",
        jwks=jwks,
    )
    claims.update(
        iss="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_pool",
        token_use="access",
        client_id="desktop-client",
    )

    assert verifier.verify(issue_token(claims))["token_use"] == "access"


@pytest.mark.parametrize(
    "override,missing",
    [
        ({"token_use": "id", "aud": "desktop-client"}, None),
        ({"token_use": "id"}, None),
        ({"client_id": "other-client"}, None),
        ({}, "aud"),
        ({}, "client_id"),
        ({}, "token_use"),
    ],
)
def test_cognito_rejects_wrong_token_profile(jwks, claims, issue_token, override, missing):
    verifier = JWTVerifier.cognito(
        user_pool_id="us-east-1_pool",
        client_id="desktop-client",
        audience="https://api.example.com",
        jwks=jwks,
    )
    claims.update(
        iss="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_pool",
        token_use="access",
        client_id="desktop-client",
    )
    claims.update(override)
    if missing:
        del claims[missing]

    with pytest.raises(InvalidClaimsError):
        verifier.verify(issue_token(claims))


def test_cognito_derives_china_partition_endpoint(http, jwks, claims, issue_token):
    issuer = "https://cognito-idp.cn-north-1.amazonaws.com.cn/cn-north-1_pool"
    http.serve(issuer + "/.well-known/jwks.json", jwks)
    verifier = JWTVerifier.cognito(
        user_pool_id="cn-north-1_pool",
        client_id="desktop-client",
        audience="https://api.example.com",
    )
    claims.update(iss=issuer, token_use="access", client_id="desktop-client")

    assert verifier.verify(issue_token(claims))["iss"] == issuer


def test_any_of_never_uses_another_issuers_keys(jwks, signing_key, claims, issue_token):
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_jwk = jwt.algorithms.RSAAlgorithm.to_jwk(other_key.public_key(), as_dict=True)
    first = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
    )
    second = JWTVerifier(
        issuer="https://other.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks={"keys": [{**other_jwk, "kid": "key-1"}]},
    )
    verifier = JWTVerifier.any_of(first, second)
    verifier.prefetch()
    assert verifier.verify(issue_token())["iss"] == "https://idp.example.com/"
    claims["iss"] = "https://other.example.com/"
    assert verifier.verify(issue_token(claims, key=other_key))["iss"] == "https://other.example.com/"
    with pytest.raises(InvalidSignatureError):
        verifier.verify(issue_token(claims, key=signing_key))


def test_any_of_rejects_unknown_issuers_without_network_requests(http, claims, issue_token):
    verifier = JWTVerifier.any_of(
        JWTVerifier(
            issuer="https://trusted.example.com/",
            audience="https://api.example.com",
            algorithms=["RS256"],
        ),
    )

    with pytest.raises(InvalidTokenError):
        verifier.verify(issue_token(claims))
    assert http.requests == []


def test_any_of_rejects_ambiguous_issuer_configuration(jwks):
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
    )

    with pytest.raises(ValueError):
        JWTVerifier.any_of(verifier, verifier)
