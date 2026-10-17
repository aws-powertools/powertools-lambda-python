"""Tests for Depends() dependency injection in function-based middleware.

Covers issue #8348: middleware should be able to declare Depends() parameters
the same way route handlers do, sharing the per-request dependency cache with
routes so a dependency used by both is resolved only once.
"""

import asyncio
import json
from typing import Annotated

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.depends import Depends
from aws_lambda_powertools.event_handler.middlewares import NextMiddleware
from aws_lambda_powertools.event_handler.request import Request
from tests.functional.utils import load_event

API_GW_V2_EVENT = load_event("apiGatewayProxyV2Event.json")


def test_middleware_depends_resolved():
    """A dependency declared by middleware is resolved and injected (issue example)."""
    app = APIGatewayHttpResolver()

    class UserDao:
        def get(self, sub: str) -> dict:
            return {"sub": sub, "name": "Jane"}

    def get_user_dao() -> UserDao:
        return UserDao()

    def user_middleware(
        app: APIGatewayHttpResolver,
        next_middleware: NextMiddleware,
        user_dao: Annotated[UserDao, Depends(get_user_dao)],
    ):
        app.append_context(user={"source": "middleware", "dao": type(user_dao).__name__})
        return next_middleware(app)

    app.use([user_middleware])

    @app.post("/my/path")
    def get_user():
        return {"user": app.context.get("user")}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"user": {"source": "middleware", "dao": "UserDao"}}


def test_middleware_depends_shared_cache_with_route():
    """The same dependency used by middleware and route is resolved only once per request."""
    app = APIGatewayHttpResolver()
    call_count = 0

    def get_config() -> dict:
        nonlocal call_count
        call_count += 1
        return {"key": "value"}

    def config_middleware(
        app: APIGatewayHttpResolver,
        next_middleware: NextMiddleware,
        config: Annotated[dict, Depends(get_config)],
    ):
        assert config == {"key": "value"}
        return next_middleware(app)

    app.use([config_middleware])

    @app.post("/my/path")
    def get_config_route(config: Annotated[dict, Depends(get_config)]):
        return {"config": config}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"config": {"key": "value"}}
    assert call_count == 1


def test_middleware_depends_overrides():
    """dependency_overrides applies to middleware dependencies too."""
    app = APIGatewayHttpResolver()

    def get_greeting() -> str:
        return "hello"

    def get_override() -> str:
        return "overridden"

    app.dependency_overrides = {get_greeting: get_override}

    def greeting_middleware(
        app: APIGatewayHttpResolver,
        next_middleware: NextMiddleware,
        greeting: Annotated[str, Depends(get_greeting)],
    ):
        app.append_context(greeting=greeting)
        return next_middleware(app)

    app.use([greeting_middleware])

    @app.post("/my/path")
    def greet():
        return {"greeting": app.context.get("greeting")}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"greeting": "overridden"}


def test_middleware_short_circuit_skips_route_dependencies():
    """A middleware that short-circuits must not trigger route dependency resolution."""
    app = APIGatewayHttpResolver()
    route_dep_called = 0

    def get_route_value() -> str:
        nonlocal route_dep_called
        route_dep_called += 1
        return "route-value"

    def auth_middleware(
        app: APIGatewayHttpResolver,
        next_middleware: NextMiddleware,
    ):
        # short-circuit: never calls next_middleware
        return {"statusCode": 401, "body": json.dumps({"message": "denied"})}

    app.use([auth_middleware])

    @app.post("/my/path")
    def protected(value: Annotated[str, Depends(get_route_value)]):
        return {"value": value}

    app(API_GW_V2_EVENT, {})
    assert route_dep_called == 0


def test_middleware_request_injection():
    """Middleware can declare a parameter typed as Request, like route handlers."""
    app = APIGatewayHttpResolver()
    seen_path = {}

    def request_middleware(
        app: APIGatewayHttpResolver,
        next_middleware: NextMiddleware,
        request: Request,
    ):
        seen_path["method"] = request.method
        return next_middleware(app)

    app.use([request_middleware])

    @app.post("/my/path")
    def check():
        return {"ok": True}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert seen_path.get("method")


def test_middleware_dependency_receives_request():
    """A dependency that declares a Request parameter receives the current request."""
    app = APIGatewayHttpResolver()

    def get_tenant(request: Request) -> str:
        return (request.headers or {}).get("x-tenant", "none")

    def tenant_middleware(
        app: APIGatewayHttpResolver,
        next_middleware: NextMiddleware,
        tenant: Annotated[str, Depends(get_tenant)],
    ):
        app.append_context(tenant=tenant)
        return next_middleware(app)

    app.use([tenant_middleware])

    @app.post("/my/path")
    def tenant():
        return {"tenant": app.context.get("tenant")}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert "tenant" in json.loads(result["body"])


def test_plain_middleware_unaffected():
    """Middleware without Depends()/Request params behaves exactly as before."""
    app = APIGatewayHttpResolver()
    called = []

    def plain_middleware(app: APIGatewayHttpResolver, next_middleware: NextMiddleware):
        called.append("middleware")
        return next_middleware(app)

    app.use([plain_middleware])

    @app.post("/my/path")
    def plain():
        return {"ok": True}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert called == ["middleware"]


def test_async_middleware_depends_resolved():
    """Async middleware with Depends() is resolved in the async chain."""
    app = APIGatewayHttpResolver()

    def get_greeting() -> str:
        return "async-hello"

    async def greeting_middleware(
        app: APIGatewayHttpResolver,
        next_middleware: NextMiddleware,
        greeting: Annotated[str, Depends(get_greeting)],
    ):
        app.append_context(greeting=greeting)
        return await next_middleware(app)

    app.use([greeting_middleware])

    @app.post("/my/path")
    async def greet():
        return {"greeting": app.context.get("greeting")}

    result = asyncio.run(app.resolve_async(API_GW_V2_EVENT, {}))
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"greeting": "async-hello"}


def test_async_sync_middleware_depends_resolved():
    """Sync middleware with Depends() works in the async chain (thread path)."""
    app = APIGatewayHttpResolver()
    call_count = 0

    def get_config() -> dict:
        nonlocal call_count
        call_count += 1
        return {"key": "value"}

    def config_middleware(
        app: APIGatewayHttpResolver,
        next_middleware: NextMiddleware,
        config: Annotated[dict, Depends(get_config)],
    ):
        assert config == {"key": "value"}
        return next_middleware(app)

    app.use([config_middleware])

    @app.post("/my/path")
    async def get_config_route(config: Annotated[dict, Depends(get_config)]):
        return {"config": config}

    result = asyncio.run(app.resolve_async(API_GW_V2_EVENT, {}))
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"config": {"key": "value"}}
    assert call_count == 1
