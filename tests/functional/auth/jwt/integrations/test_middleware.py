import copy
import json

import pytest

from aws_lambda_powertools.event_handler import (
    ALBResolver,
    APIGatewayHttpResolver,
    APIGatewayRestResolver,
    LambdaFunctionUrlResolver,
    Response,
)
from aws_lambda_powertools.utilities.auth import JWTVerifier
from tests.functional.utils import load_event


@pytest.fixture(params=["http", "rest"])
def resolver_event(request):
    if request.param == "http":
        return APIGatewayHttpResolver(), copy.deepcopy(load_event("apiGatewayProxyV2Event_GET.json"))
    return APIGatewayRestResolver(), copy.deepcopy(load_event("apiGatewayProxyEvent.json"))


def make_verifier(jwks):
    return JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks=jwks,
    )


def challenge(response):
    if "headers" in response:
        return response["headers"]["WWW-Authenticate"]
    return response["multiValueHeaders"]["WWW-Authenticate"][0]


def test_middleware_exposes_only_verified_claims_and_clears_context(resolver_event, jwks, issue_token):
    app, event = resolver_event
    verifier = make_verifier(jwks)

    @app.get("/my/path", middlewares=[verifier.require(scopes=["orders:read"])])
    def orders():
        return {"subject": app.context["claims"]["sub"]}

    event["headers"] = {"AUTHORIZATION": "bEaReR " + issue_token()}
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"subject": "user-123"}
    assert "claims" not in app.context

    event["headers"] = {}
    assert app.resolve(event, {})["statusCode"] == 401


@pytest.mark.parametrize("public_first", [True, False])
def test_failed_handler_cannot_leak_claims_into_later_invocations(
    resolver_event,
    jwks,
    issue_token,
    claims,
    public_first,
):
    app, event = resolver_event
    should_fail = True
    error_contexts = []

    def on_error(error):
        error_contexts.append(dict(app.context))
        return Response(status_code=error.status_code, content_type="application/json", body={})

    @app.get("/my/path", middlewares=[make_verifier(jwks).require(on_error=on_error)])
    def orders():
        if should_fail:
            app.append_context(application_value="preserved")
            raise RuntimeError("handler failed")
        return {"subject": app.context["claims"]["sub"]}

    @app.get("/public")
    def public():
        return {"claims": app.context.get("claims")}

    event["headers"] = {"authorization": "Bearer " + issue_token()}
    with pytest.raises(RuntimeError, match="handler failed"):
        app.resolve(event, {})
    assert "claims" not in app.context
    assert app.context["application_value"] == "preserved"

    event["headers"] = {}
    public_event = copy.deepcopy(event)
    public_event["path"] = public_event["rawPath"] = "/public"
    if "http" in public_event["requestContext"]:
        public_event["requestContext"]["http"]["path"] = "/public"
    following_requests = [(public_event, 200), (event, 401)]
    if not public_first:
        following_requests.reverse()
    for next_event, status in following_requests:
        response = app.resolve(next_event, {})
        assert response["statusCode"] == status
        if status == 200:
            assert json.loads(response["body"]) == {"claims": None}
    assert all("claims" not in context for context in error_contexts)

    should_fail = False
    claims["sub"] = "another-user"
    event["headers"] = {"authorization": "Bearer " + issue_token(claims)}
    response = app.resolve(event, {})
    assert json.loads(response["body"]) == {"subject": "another-user"}
    assert "claims" not in app.context


def test_downstream_middleware_can_use_claims_before_and_after_handler(resolver_event, jwks, issue_token):
    app, event = resolver_event
    subjects = []

    def downstream(app, next_middleware):
        subjects.append(app.context["claims"]["sub"])
        response = next_middleware(app)
        subjects.append(app.context["claims"]["sub"])
        return response

    @app.get("/my/path", middlewares=[make_verifier(jwks).require(), downstream])
    def orders():
        return {"subject": app.context["claims"]["sub"]}

    event["headers"] = {"authorization": "Bearer " + issue_token()}
    assert app.resolve(event, {})["statusCode"] == 200
    assert subjects == ["user-123", "user-123"]
    assert "claims" not in app.context


@pytest.mark.parametrize(
    "header,status,expected_challenge",
    [
        (None, 401, "Bearer"),
        ("Basic credentials", 401, 'Bearer error="invalid_token"'),
        ("Bearer not-a-token", 401, 'Bearer error="invalid_token"'),
        ("Bearer one two", 401, 'Bearer error="invalid_token"'),
        (["Bearer token"], 401, 'Bearer error="invalid_token"'),
    ],
)
def test_middleware_denies_invalid_credentials_without_calling_handler(
    resolver_event,
    jwks,
    header,
    status,
    expected_challenge,
):
    app, event = resolver_event

    @app.get("/my/path", middlewares=[make_verifier(jwks).require()])
    def orders():
        pytest.fail("An unauthenticated handler must not run")

    event["headers"] = {} if header is None else {"authorization": header}
    response = app.resolve(event, {})
    assert response["statusCode"] == status
    assert challenge(response) == expected_challenge
    assert json.loads(response["body"]) == {"message": "Unauthorized"}


@pytest.mark.parametrize(
    "scope_claims,status",
    [
        ({"scope": "orders:read orders:write"}, 200),
        ({"scp": "orders:read"}, 200),
        ({"scopes": ["orders:read"]}, 200),
        ({"scope": ["orders:read"]}, 200),
        ({"scope": "orders:write"}, 403),
        ({}, 403),
        ({"scope": None, "scp": "orders:read"}, 401),
        ({"scope": ["orders:read", 42]}, 401),
        ({"scope": "orders:write", "scp": "orders:read"}, 403),
    ],
)
def test_scope_formats_and_precedence(resolver_event, jwks, claims, issue_token, scope_claims, status):
    app, event = resolver_event
    claims.pop("scope")
    claims.update(scope_claims)

    @app.get("/my/path", middlewares=[make_verifier(jwks).require(scopes=["orders:read"])])
    def orders():
        return {"ok": True}

    event["headers"] = {"authorization": "Bearer " + issue_token(claims)}
    response = app.resolve(event, {})
    assert response["statusCode"] == status
    if status == 403:
        assert challenge(response) == 'Bearer error="insufficient_scope", scope="orders:read"'


def test_custom_error_response_preserves_status_and_challenge(resolver_event, jwks, issue_token):
    app, event = resolver_event
    verifier = make_verifier(jwks)

    def on_error(error):
        return Response(
            status_code=error.status_code,
            content_type="application/json",
            body={"error": "access_denied"},
            headers=error.headers,
        )

    @app.get("/my/path", middlewares=[verifier.require(scopes=["admin"], on_error=on_error)])
    def orders():
        pytest.fail("An error callback must not execute the protected route")

    event["headers"] = {"authorization": "Bearer " + issue_token()}
    response = app.resolve(event, {})
    assert response["statusCode"] == 403
    assert json.loads(response["body"]) == {"error": "access_denied"}
    assert "insufficient_scope" in challenge(response)


def test_additional_authorization_must_return_true(resolver_event, jwks, issue_token):
    app, event = resolver_event

    @app.get("/my/path", middlewares=[make_verifier(jwks).require(authorize=lambda claims: False)])
    def orders():
        pytest.fail("A forbidden handler must not run")

    event["headers"] = {"authorization": "Bearer " + issue_token()}
    assert app.resolve(event, {})["statusCode"] == 403


def test_unavailable_keys_return_generic_503(resolver_event, http, issue_token):
    app, event = resolver_event
    http.serve("https://idp.example.com/keys", {"error": "private provider diagnostics"}, status=503)
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks_uri="https://idp.example.com/keys",
    )

    @app.get("/my/path", middlewares=[verifier.require()])
    def orders():
        pytest.fail("A handler must not run without trusted keys")

    event["headers"] = {"authorization": "Bearer " + issue_token()}
    response = app.resolve(event, {})
    assert response["statusCode"] == 503
    assert json.loads(response["body"]) == {"message": "Service Unavailable"}


def test_public_routes_do_not_require_credentials(resolver_event):
    app, event = resolver_event

    @app.get("/my/path")
    def health():
        return {"status": "ok"}

    event["headers"] = {}
    assert app.resolve(event, {})["statusCode"] == 200


@pytest.mark.parametrize(
    "headers,multi_headers,status",
    [
        (None, {"Authorization": ["TOKEN"]}, 200),
        ({"authorization": "TOKEN"}, {"Authorization": ["TOKEN"]}, 200),
        (None, {"Authorization": ["TOKEN", "TOKEN"]}, 401),
        ({"authorization": "TOKEN"}, {"Authorization": ["Bearer another"]}, 401),
        (None, {"Authorization": "TOKEN"}, 401),
    ],
)
def test_alb_multi_value_authorization_is_unambiguous(jwks, issue_token, headers, multi_headers, status):
    app = ALBResolver()
    event = copy.deepcopy(load_event("albMultiValueHeadersEvent.json"))
    token = "Bearer " + issue_token()
    event["headers"] = json.loads(json.dumps(headers).replace("TOKEN", token))
    event["multiValueHeaders"] = json.loads(json.dumps(multi_headers).replace("TOKEN", token))

    @app.get("/todos", middlewares=[make_verifier(jwks).require()])
    def orders():
        return {"subject": app.context["claims"]["sub"]}

    response = app.resolve(event, {})
    assert response["statusCode"] == status
    if status == 200:
        assert json.loads(response["body"]) == {"subject": "user-123"}


def test_function_url_middleware(jwks, issue_token):
    app = LambdaFunctionUrlResolver()
    event = copy.deepcopy(load_event("lambdaFunctionUrlEvent.json"))
    event["headers"] = {"authorization": "Bearer " + issue_token()}

    @app.get("/", middlewares=[make_verifier(jwks).require()])
    def orders():
        return {"subject": app.context["claims"]["sub"]}

    assert app.resolve(event, {})["statusCode"] == 200
