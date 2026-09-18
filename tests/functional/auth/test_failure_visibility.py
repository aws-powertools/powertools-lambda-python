import copy
import json
import time

import pytest

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Response
from aws_lambda_powertools.utilities.auth import AuthErrorContext, AuthFailureReason, JWTVerifier
from aws_lambda_powertools.utilities.auth.exceptions import JWKSFetchError
from tests.functional.utils import load_event

ARN = "arn:aws:execute-api:us-east-1:123456789012:api123/prod/GET/orders"
REASONS = [
    "missing_token",
    "invalid_token",
    "invalid_claims",
    "token_expired",
    "invalid_signature",
    "insufficient_scope",
    "forbidden",
    "jwks_unavailable",
]


def failure_case(reason, jwks, claims, issue_token, http):
    options = {"jwks": jwks}
    scopes = ["admin"] if reason == "insufficient_scope" else []
    if reason == "invalid_claims":
        claims["aud"] = "private-incorrect-audience"
    elif reason == "token_expired":
        claims["exp"] = int(time.time()) - 120
    elif reason == "jwks_unavailable":
        url = "https://idp.example.com/keys"
        http.serve(url, {"private": "provider-response"}, status=503)
        options = {"jwks_uri": url}
    token = issue_token(claims)
    if reason == "missing_token":
        token = None
    elif reason == "invalid_token":
        token = "private-invalid-token"
    elif reason == "invalid_signature":
        token = token.rsplit(".", 1)[0] + ".AAAA"
    subject = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        **options,
    )
    return subject, token, scopes


@pytest.mark.parametrize("reason", REASONS)
def test_middleware_reports_safe_reasons_without_exposing_them_in_responses(
    jwks,
    claims,
    issue_token,
    http,
    reason,
    caplog,
):
    subject, token, scopes = failure_case(reason, jwks, claims, issue_token, http)
    app = APIGatewayHttpResolver()
    observations = []

    def on_error(context: AuthErrorContext):
        observations.append(context)
        return Response(
            status_code=context.status_code,
            content_type="application/json",
            body={"message": "Denied"},
            headers=context.headers,
        )

    middleware = subject.require(
        scopes=scopes,
        authorize=lambda claims: reason != "forbidden",
        on_error=on_error,
    )

    @app.get("/my/path", middlewares=[middleware])
    def protected():
        pytest.fail("A rejected request must never reach the protected handler")

    event = copy.deepcopy(load_event("apiGatewayProxyV2Event_GET.json"))
    event["headers"] = {} if token is None else {"authorization": "Bearer " + token}
    response = app.resolve(event, {})
    assert len(observations) == 1
    context = observations[0]
    assert context.reason is AuthFailureReason(reason)
    assert isinstance(context.reason, str)
    assert json.dumps(context.reason) == json.dumps(reason)
    assert context.retryable is (reason == "jwks_unavailable")
    assert response["statusCode"] == (
        503 if context.retryable else 403 if reason in ("insufficient_scope", "forbidden") else 401
    )
    assert json.loads(response["body"]) == {"message": "Denied"}
    assert "private" not in repr(context)
    assert "claims" not in app.context
    assert caplog.records == []


@pytest.mark.parametrize("reason", [reason for reason in REASONS if reason != "forbidden"])
@pytest.mark.parametrize("response_format", ["iam", "simple"])
def test_authorizer_reports_safe_reasons_and_preserves_denial_or_invocation_failure(
    jwks,
    claims,
    issue_token,
    http,
    reason,
    response_format,
    caplog,
):
    subject, token, scopes = failure_case(reason, jwks, claims, issue_token, http)
    event = {"type": "REQUEST", "version": "2.0", "routeArn": ARN}
    event["headers"] = {} if token is None else {"authorization": "Bearer " + token}
    observations = []

    def on_error(error):
        assert error.__context__ is None
        assert error.__cause__ is None
        observations.append((error.reason, error.retryable))
        return {"isAuthorized": True}  # A callback cannot turn a failure into an Allow.

    # Sanitization must also hold when the owner is handling another exception.
    try:
        raise ValueError("private-caller-error")
    except ValueError:
        if reason == "jwks_unavailable":
            with pytest.raises(JWKSFetchError) as error:
                subject.authorize(event, scopes=scopes, response_format=response_format, on_error=on_error)
            assert error.value.__context__ is None
        else:
            response = subject.authorize(event, scopes=scopes, response_format=response_format, on_error=on_error)
            if response_format == "simple":
                assert response["isAuthorized"] is False
            else:
                assert response["policyDocument"]["Statement"][0]["Effect"] == "Deny"
            assert "context" not in response or response["context"] == {}
            assert "reason" not in response
            assert "retryable" not in response
    assert observations == [(AuthFailureReason(reason), reason == "jwks_unavailable")]
    assert caplog.records == []


def test_authorizer_does_not_report_success_as_an_error(jwks, claims, issue_token, http):
    subject, token, _ = failure_case("valid", jwks, claims, issue_token, http)
    event = {"type": "TOKEN", "methodArn": ARN, "authorizationToken": "Bearer " + token}
    errors = []
    response = subject.authorize(event, on_error=errors.append)
    assert response["policyDocument"]["Statement"][0]["Effect"] == "Allow"
    assert errors == []


def test_authorizer_error_callback_failure_cannot_allow_a_request(jwks, claims, issue_token, http):
    subject, _, _ = failure_case("missing_token", jwks, claims, issue_token, http)

    def on_error(error):
        raise RuntimeError("Application metrics failed")

    event = {"type": "TOKEN", "methodArn": ARN}
    with pytest.raises(RuntimeError, match="Application metrics failed"):
        subject.authorize(event, on_error=on_error)
