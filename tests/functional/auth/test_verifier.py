import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from aws_lambda_powertools.utilities.auth import JWTVerifier
from aws_lambda_powertools.utilities.auth.exceptions import (
    InvalidClaimsError,
    InvalidSignatureError,
    InvalidTokenError,
    TokenExpiredError,
)


def test_verify_access_token_with_static_keys(jwks, claims, issue_token):
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
    )

    assert verifier.verify(issue_token()) == claims


@pytest.mark.parametrize("missing", ["iss", "aud", "exp", "sub"])
def test_required_claims_are_additive(jwks, claims, issue_token, missing):
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
        required_claims=["sub"],
    )
    del claims[missing]

    with pytest.raises(InvalidClaimsError):
        verifier.verify(issue_token(claims))


def test_expired_token_is_rejected(jwks, claims, issue_token):
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
        clock_skew_seconds=0,
    )
    claims["exp"] = int(time.time()) - 1

    with pytest.raises(TokenExpiredError):
        verifier.verify(issue_token(claims))


@pytest.mark.parametrize(
    "claim,value",
    [
        ("iss", "https://another.example.com/"),
        ("iss", "https://idp.example.com"),
        ("aud", "https://another.example.com"),
        ("aud", []),
        ("aud", ["https://api.example.com", 42]),
        ("exp", "9999999999"),
        ("exp", float("inf")),
        ("exp", float("nan")),
        ("exp", True),
        ("nbf", "0"),
        ("nbf", 9999999999),
    ],
)
def test_invalid_claim_values_are_rejected(jwks, claims, issue_token, claim, value):
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
    )
    claims[claim] = value

    with pytest.raises(InvalidClaimsError):
        verifier.verify(issue_token(claims))


@pytest.mark.parametrize(
    "option,value",
    [
        ("issuer", "http://idp.example.com"),
        ("issuer", "https://user:secret@idp.example.com"),
        ("issuer", "https://idp.example.com/#fragment"),
        ("audience", ""),
        ("audience", []),
        ("algorithms", []),
        ("algorithms", ["none"]),
        ("algorithms", ["HS256"]),
        ("algorithms", ["RS256", "HS256"]),
        ("clock_skew_seconds", -1),
        ("clock_skew_seconds", float("inf")),
        ("required_claims", ""),
    ],
)
def test_invalid_verifier_configuration_is_rejected(jwks, option, value):
    options = {
        "issuer": "https://idp.example.com/",
        "audience": "https://api.example.com",
        "algorithms": ["RS256"],
        "jwks": jwks,
        option: value,
    }

    with pytest.raises(ValueError):
        JWTVerifier(**options)


@pytest.mark.parametrize("token", ["", "not-a-jwt", "a.b.c", None, 42])
def test_malformed_tokens_raise_redacted_errors(jwks, token):
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
    )

    with pytest.raises(InvalidTokenError) as error:
        verifier.verify(token)
    assert str(error.value) == "Invalid access token"


@pytest.mark.parametrize("key_change", [{"alg": "RS512"}, {"use": "enc"}, {"key_ops": ["sign"]}])
def test_signing_key_metadata_is_enforced(jwks, issue_token, key_change):
    jwks["keys"][0].update(key_change)
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
    )

    with pytest.raises(InvalidTokenError):
        verifier.verify(issue_token())


def test_disallowed_token_algorithm_is_rejected(jwks, claims):
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
    )
    token = jwt.encode(claims, "a-separate-signing-secret-with-32-bytes", algorithm="HS256", headers={"kid": "key-1"})

    with pytest.raises(InvalidTokenError):
        verifier.verify(token)


def test_static_key_configuration_is_copied(jwks, issue_token):
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
    )
    jwks["keys"].clear()

    assert verifier.verify(issue_token())["sub"] == "user-123"


@pytest.mark.parametrize("algorithm", ["PS256", "ES256", "EdDSA"])
def test_asymmetric_algorithm_families(algorithm, signing_key, claims):
    if algorithm == "ES256":
        key = ec.generate_private_key(ec.SECP256R1())
    elif algorithm == "EdDSA":
        key = ed25519.Ed25519PrivateKey.generate()
    else:
        key = signing_key
    algorithm_impl = jwt.get_algorithm_by_name(algorithm)
    public_jwk = algorithm_impl.to_jwk(key.public_key(), as_dict=True)
    verifier = JWTVerifier(
        issuer=claims["iss"],
        audience=claims["aud"],
        algorithms=[algorithm],
        jwks={"keys": [{**public_jwk, "kid": "key-1"}]},
    )
    token = jwt.encode(claims, key, algorithm=algorithm, headers={"kid": "key-1"})

    assert verifier.verify(token) == claims


def test_private_jwk_is_rejected_without_exposing_key(signing_key, claims, issue_token):
    private_jwk = jwt.algorithms.RSAAlgorithm.to_jwk(signing_key, as_dict=True)
    verifier = JWTVerifier(
        issuer=claims["iss"],
        audience=claims["aud"],
        algorithms=["RS256"],
        jwks={"keys": [{**private_jwk, "kid": "key-1"}]},
    )

    with pytest.raises(InvalidTokenError) as error:
        verifier.verify(issue_token())
    assert private_jwk["d"] not in str(error.value)


def test_invalid_signature_has_stable_error(jwks, claims, signing_key, issue_token):
    # This payload is valid, but the signature belongs to the original payload.
    token = issue_token().split(".")
    claims["sub"] = "another-user"
    token[1] = jwt.encode(claims, signing_key, algorithm="RS256").split(".")[1]
    verifier = JWTVerifier(
        issuer=claims["iss"],
        audience=claims["aud"],
        algorithms=["RS256"],
        jwks=jwks,
    )

    with pytest.raises(InvalidSignatureError) as error:
        verifier.verify(".".join(token))
    assert str(error.value) == "Invalid access token signature"


@pytest.mark.parametrize("key_change", [{"n": None}, {"kty": []}, {"crv": "P-384", "kty": "EC"}])
def test_malformed_key_material_fails_closed(jwks, issue_token, key_change):
    jwks["keys"][0].update(key_change)
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
    )
    with pytest.raises(InvalidTokenError):
        verifier.verify(issue_token())


def test_ec_curve_must_match_algorithm(claims, issue_token):
    key = ec.generate_private_key(ec.SECP384R1())
    public_jwk = jwt.algorithms.ECAlgorithm.to_jwk(key.public_key(), as_dict=True)
    verifier = JWTVerifier(
        issuer=claims["iss"],
        audience=claims["aud"],
        algorithms=["ES256"],
        jwks={"keys": [{**public_jwk, "kid": "key-1"}]},
    )
    header = jwt.utils.base64url_encode(b'{"alg":"ES256","kid":"key-1"}')
    payload = issue_token().split(".")[1].encode()
    message = header + b"." + payload
    signature = jwt.algorithms.ECAlgorithm(jwt.algorithms.ECAlgorithm.SHA256).sign(message, key)
    token = (message + b"." + jwt.utils.base64url_encode(signature)).decode()

    with pytest.raises(InvalidTokenError):
        verifier.verify(token)


@pytest.mark.parametrize("issuer_group", [False, True])
@pytest.mark.parametrize("nested_part", ["header", "payload"])
def test_excessively_nested_token_json_raises_sanitized_error(jwks, signing_key, issuer_group, nested_part):
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
    )
    if issuer_group:
        verifier = JWTVerifier.any_of(verifier)
    nested = b'{"nested":' + b"[" * 2000 + b"0" + b"]" * 2000 + b"}"
    header = nested if nested_part == "header" else b'{"alg":"RS256","kid":"key-1"}'
    payload = nested if nested_part == "payload" else b'{"iss":"https://idp.example.com/"}'
    message = b".".join((jwt.utils.base64url_encode(header), jwt.utils.base64url_encode(payload)))
    signature = jwt.get_algorithm_by_name("RS256").sign(message, signing_key)
    token = (message + b"." + jwt.utils.base64url_encode(signature)).decode()

    with pytest.raises(InvalidTokenError):
        verifier.verify(token)
