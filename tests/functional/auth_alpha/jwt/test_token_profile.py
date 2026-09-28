import copy
import json

import pytest

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.utilities.auth_alpha import JWTVerifier
from aws_lambda_powertools.utilities.auth_alpha.jwt.exceptions import InvalidClaimsError, InvalidSignatureError
from tests.functional.utils import load_event

ARN = "arn:aws:execute-api:us-east-1:123456789012:api123/prod/GET/orders"


def verifier(jwks, **options):
    return JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
        **options,
    )


@pytest.mark.parametrize("surface", ["direct", "group", "middleware", "iam", "simple"])
@pytest.mark.parametrize("profile", ["valid", "wrong-purpose", "missing-purpose", "wrong-header", "missing-header"])
def test_profile_constraints_apply_to_every_verification_surface(jwks, claims, issue_token, surface, profile):
    subject = verifier(
        jwks,
        expected_claims={"token_use": "access"},
        expected_headers={"typ": "at+jwt"},
    )
    claims["token_use"] = "id" if profile == "wrong-purpose" else "access"
    if profile == "missing-purpose":
        del claims["token_use"]
    header_type = "JWT" if profile == "wrong-header" else None if profile == "missing-header" else "at+jwt"
    token = issue_token(claims, headers={"typ": header_type})
    accepted = profile == "valid"
    if surface in ("direct", "group"):
        subject = JWTVerifier.any_of(subject) if surface == "group" else subject
        if accepted:
            assert subject.verify(token)["sub"] == claims["sub"]
        else:
            with pytest.raises(InvalidClaimsError):
                subject.verify(token)
    elif surface == "middleware":
        app = APIGatewayHttpResolver()

        @app.get("/my/path", middlewares=[subject.require()])
        def protected():
            assert accepted, "A token for another purpose reached the protected handler"
            return {"subject": app.context["claims"]["sub"]}

        event = copy.deepcopy(load_event("apiGatewayProxyV2Event_GET.json"))
        event["headers"] = {"authorization": "Bearer " + token}
        response = app.resolve(event, {})
        assert response["statusCode"] == (200 if accepted else 401)
        if accepted:
            assert json.loads(response["body"]) == {"subject": claims["sub"]}
    else:
        event = {
            "type": "REQUEST",
            "version": "2.0",
            "routeArn": ARN,
            "headers": {"authorization": "Bearer " + token},
        }
        response = subject.authorize(event, response_format=surface)
        if surface == "simple":
            assert response["isAuthorized"] is accepted
        else:
            assert response["policyDocument"]["Statement"][0]["Effect"] == ("Allow" if accepted else "Deny")


@pytest.mark.parametrize("field", ["expected_claims", "expected_headers"])
@pytest.mark.parametrize("value", [[], "token_use", {"": "access"}, {"token_use": ""}, {"typ": 1}, {1: "access"}])
def test_profile_configuration_requires_named_string_values(jwks, field, value):
    with pytest.raises(ValueError, match="Expected claims and headers"):
        verifier(jwks, **{field: value})


def test_profile_configuration_is_copied_and_never_weakens_signature_checks(jwks, claims, issue_token):
    expected_claims = {"token_use": "access"}
    expected_headers = {"typ": "at+jwt"}
    subject = verifier(jwks, expected_claims=expected_claims, expected_headers=expected_headers)
    expected_claims["token_use"] = "id"
    expected_headers["typ"] = "JWT"
    claims["token_use"] = "access"
    token = issue_token(claims, headers={"typ": "at+jwt"})
    assert subject.verify(token)["token_use"] == "access"
    tampered = token.rsplit(".", 1)[0] + ".AAAA"
    with pytest.raises(InvalidSignatureError):
        subject.verify(tampered)
    claims["token_use"] = "id"
    wrong_purpose = issue_token(claims, headers={"typ": "at+jwt"})
    with pytest.raises(InvalidClaimsError):
        subject.verify(wrong_purpose)


def test_generic_constraints_cannot_override_the_cognito_profile(jwks, claims, issue_token):
    issuer = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_pool"
    subject = JWTVerifier.cognito(
        user_pool_id="us-east-1_pool",
        client_id="desktop-client",
        audience=claims["aud"],
        jwks=jwks,
        expected_claims={"token_use": "id"},
    )
    claims.update(iss=issuer, token_use="id", client_id="desktop-client")
    token = issue_token(claims)
    with pytest.raises(InvalidClaimsError):
        subject.verify(token)
