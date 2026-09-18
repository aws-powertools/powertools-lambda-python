import copy

import pytest

from aws_lambda_powertools.utilities.auth import JWTVerifier
from aws_lambda_powertools.utilities.auth.exceptions import JWKSFetchError
from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    APIGatewayAuthorizerEventV2,
    APIGatewayAuthorizerRequestEvent,
    APIGatewayAuthorizerTokenEvent,
)
from tests.functional.utils import load_event

ARN = "arn:aws:execute-api:us-east-1:123456789012:api123/prod/GET/orders/123"


@pytest.fixture(params=["token", "rest-request", "http-v1", "http-v2"])
def authorizer_event(request, issue_token):
    if request.param == "token":
        return APIGatewayAuthorizerTokenEvent(
            {"type": "TOKEN", "methodArn": ARN, "authorizationToken": "Bearer " + issue_token()},
        )
    event = {"type": "REQUEST", "headers": {"Authorization": "Bearer " + issue_token()}}
    if request.param == "http-v2":
        return APIGatewayAuthorizerEventV2({**event, "version": "2.0", "routeArn": ARN})
    if request.param == "http-v1":
        event["version"] = "1.0"
    return APIGatewayAuthorizerRequestEvent({**event, "methodArn": ARN})


def verifier(jwks):
    return JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
    )


def test_iam_authorizer_allows_only_the_requested_arn(authorizer_event, jwks):
    response = verifier(jwks).authorize(authorizer_event, scopes=["orders:read"], context_claims=["sub"])

    assert response == {
        "principalId": "user-123",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{"Action": "execute-api:Invoke", "Effect": "Allow", "Resource": [ARN]}],
        },
        "context": {"sub": "user-123"},
    }


def test_iam_authorizer_denies_missing_scopes_without_forwarding_claims(authorizer_event, jwks):
    response = verifier(jwks).authorize(authorizer_event, scopes=["orders:write"], context_claims=["sub"])

    assert response["policyDocument"]["Statement"] == [
        {"Action": "execute-api:Invoke", "Effect": "Deny", "Resource": [ARN]},
    ]
    assert "context" not in response


def test_iam_authorizer_requires_a_nonempty_subject(jwks, claims, issue_token):
    claims.pop("sub")
    event = {"type": "TOKEN", "methodArn": ARN, "authorizationToken": "Bearer " + issue_token(claims)}

    assert verifier(jwks).authorize(event)["policyDocument"]["Statement"][0]["Effect"] == "Deny"


@pytest.mark.parametrize("authorization", [None, "Basic secret", "Bearer invalid"])
def test_iam_authorizer_denies_invalid_tokens(jwks, authorization):
    event = {"type": "TOKEN", "methodArn": ARN, "authorizationToken": authorization}

    assert verifier(jwks).authorize(event)["policyDocument"]["Statement"][0]["Effect"] == "Deny"


def test_simple_authorizer_uses_boolean_response(jwks, issue_token):
    event = {
        "type": "REQUEST",
        "version": "2.0",
        "routeArn": ARN,
        "headers": {"authorization": "Bearer " + issue_token()},
    }

    assert verifier(jwks).authorize(event, response_format="simple", context_claims=["sub"]) == {
        "isAuthorized": True,
        "context": {"sub": "user-123"},
    }
    assert verifier(jwks).authorize(event, response_format="simple", scopes=["admin"]) == {"isAuthorized": False}


def test_simple_responses_require_payload_version_two(jwks, issue_token):
    event = {
        "type": "REQUEST",
        "version": "1.0",
        "methodArn": ARN,
        "headers": {"authorization": "Bearer " + issue_token()},
    }

    with pytest.raises(ValueError):
        verifier(jwks).authorize(event, response_format="simple")


def test_context_is_opt_in_and_copies_only_selected_scalar_claims(jwks, claims, issue_token):
    claims.update(roles=["admin"], profile={"private": "data"}, enabled=True, limit=3, ratio=0.5)
    event = {"type": "TOKEN", "methodArn": ARN, "authorizationToken": "Bearer " + issue_token(claims)}
    subject = verifier(jwks)

    assert "context" not in subject.authorize(event)
    assert subject.authorize(event, context_claims=["sub", "roles", "profile", "enabled", "limit", "ratio", "missing"])[
        "context"
    ] == {"sub": "user-123", "enabled": True, "limit": 3, "ratio": 0.5}


def test_preserves_partition_and_encoded_resource_paths(jwks, issue_token):
    arn = "arn:aws-cn:execute-api:cn-north-1:123456789012:api123/$default/GET/orders/a%20b:detail"
    event = {"type": "TOKEN", "methodArn": arn, "authorizationToken": "Bearer " + issue_token()}

    assert verifier(jwks).authorize(event)["policyDocument"]["Statement"][0]["Resource"] == [arn]


def test_authorizer_does_not_convert_unavailable_keys_into_an_allow(http, issue_token):
    http.serve("https://idp.example.com/keys", {}, status=503)
    subject = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks_uri="https://idp.example.com/keys",
    )
    event = {"type": "TOKEN", "methodArn": ARN, "authorizationToken": "Bearer " + issue_token()}

    with pytest.raises(JWKSFetchError):
        subject.authorize(event)


@pytest.mark.parametrize("wrapped", [False, True])
@pytest.mark.parametrize(
    "fixture,wrapper",
    [
        ("apiGatewayAuthorizerTokenEvent.json", APIGatewayAuthorizerTokenEvent),
        ("apiGatewayAuthorizerRequestEvent.json", APIGatewayAuthorizerRequestEvent),
        ("apiGatewayAuthorizerV2Event.json", APIGatewayAuthorizerEventV2),
    ],
)
def test_gateway_event_fixtures_produce_exact_allow_and_deny_policies(jwks, issue_token, wrapped, fixture, wrapper):
    event = copy.deepcopy(load_event(fixture))
    is_token = event["type"] == "TOKEN"
    if is_token:
        # The existing TOKEN fixture uses a policy wildcard. Incoming requests
        # need a concrete stage for this helper's request-specific policy.
        event["methodArn"] = event["methodArn"].replace("/*/", "/test/")
        event["authorizationToken"] = "Bearer " + issue_token()
    else:
        event["headers"]["Authorization"] = "Bearer " + issue_token()
    arn = event.get("routeArn", event.get("methodArn"))
    subject = verifier(jwks)

    response = subject.authorize(wrapper(event) if wrapped else event, context_claims=["sub"])
    assert response["policyDocument"]["Statement"] == [
        {"Action": "execute-api:Invoke", "Effect": "Allow", "Resource": [arn]},
    ]
    assert response["context"] == {"sub": "user-123"}

    if is_token:
        event["authorizationToken"] = "Bearer invalid"
    else:
        event["headers"]["Authorization"] = "Bearer invalid"
    response = subject.authorize(wrapper(event) if wrapped else event, context_claims=["sub"])
    assert response["policyDocument"]["Statement"] == [
        {"Action": "execute-api:Invoke", "Effect": "Deny", "Resource": [arn]},
    ]
    assert "context" not in response


@pytest.mark.parametrize("route_key", ["GET /merchants", "$default"])
def test_http_v2_fixture_supports_simple_responses_and_keeps_route_arn(jwks, issue_token, route_key):
    event = copy.deepcopy(load_event("apiGatewayAuthorizerV2Event.json"))
    event["routeKey"] = event["requestContext"]["routeKey"] = route_key
    event["headers"]["Authorization"] = "Bearer " + issue_token()
    subject = verifier(jwks)
    assert subject.authorize(event, response_format="simple") == {"isAuthorized": True}
    assert subject.authorize(event)["policyDocument"]["Statement"][0]["Resource"] == [event["routeArn"]]
    event["headers"].pop("Authorization")
    assert subject.authorize(event, response_format="simple") == {"isAuthorized": False}


@pytest.mark.parametrize("arn", [None, "", "not-an-arn", ARN.replace("/prod/", "/*/"), ARN + "?"])
def test_invalid_request_arns_raise_instead_of_returning_an_invalid_policy(jwks, issue_token, arn):
    event = copy.deepcopy(load_event("apiGatewayAuthorizerTokenEvent.json"))
    event["authorizationToken"] = "Bearer " + issue_token()
    event["methodArn"] = arn
    with pytest.raises(ValueError, match="concrete API Gateway"):
        verifier(jwks).authorize(event)


@pytest.mark.parametrize("malformed", [False, True])
@pytest.mark.parametrize("field", ["headers", "multiValueHeaders"])
def test_authorizer_denies_malformed_or_ambiguous_header_maps(jwks, issue_token, malformed, field):
    token = "Bearer " + issue_token()
    value = [token] if field == "multiValueHeaders" else token
    headers = [("Authorization", value)] if malformed else {"Authorization": value, "authorization": value}
    event = {"type": "REQUEST", "methodArn": ARN, field: headers}
    response = verifier(jwks).authorize(event)
    assert response["principalId"] == "unauthorized"
    assert response["policyDocument"]["Statement"][0]["Effect"] == "Deny"
    assert "context" not in response


@pytest.mark.parametrize("event", [None, [], {}, {"type": "OTHER"}])
def test_authorizer_rejects_unsupported_events(jwks, event):
    with pytest.raises(ValueError, match="TOKEN or REQUEST"):
        verifier(jwks).authorize(event)


@pytest.mark.parametrize(
    "options,message",
    [
        ({"response_format": "unsupported"}, "response_format"),
        ({"context_claims": ["claims"]}, "claims is reserved"),
    ],
)
def test_authorizer_rejects_invalid_response_configuration(jwks, issue_token, options, message):
    event = {"type": "TOKEN", "methodArn": ARN, "authorizationToken": "Bearer " + issue_token()}
    with pytest.raises(ValueError, match=message):
        verifier(jwks).authorize(event, **options)
