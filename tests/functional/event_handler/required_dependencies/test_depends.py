"""Tests for the Depends() dependency injection feature using Annotated."""

import asyncio
import json
from typing import Annotated

import pytest

from aws_lambda_powertools.event_handler import (
    ALBResolver,
    APIGatewayHttpResolver,
    APIGatewayRestResolver,
    Response,
    VPCLatticeV2Resolver,
    content_types,
)
from aws_lambda_powertools.event_handler.depends import DependencyResolutionError, Depends
from aws_lambda_powertools.event_handler.exceptions import UnauthorizedError
from aws_lambda_powertools.event_handler.request import Request
from tests.functional.utils import load_event

API_GW_V2_EVENT = load_event("apiGatewayProxyV2Event.json")


def test_depends_simple():
    """A simple dependency is resolved and injected into the handler."""
    app = APIGatewayHttpResolver()

    def get_greeting() -> str:
        return "hello"

    @app.post("/my/path")
    def handler(greeting: Annotated[str, Depends(get_greeting)]):
        return {"greeting": greeting}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"greeting": "hello"}


def test_depends_nested():
    """Dependencies can depend on other dependencies."""
    app = APIGatewayHttpResolver()

    def get_prefix() -> str:
        return "Hello"

    def get_greeting(prefix: Annotated[str, Depends(get_prefix)]) -> str:
        return f"{prefix}, world!"

    @app.post("/my/path")
    def handler(greeting: Annotated[str, Depends(get_greeting)]):
        return {"greeting": greeting}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"greeting": "Hello, world!"}


def test_depends_cache_per_invocation():
    """Same dependency used twice in one invocation is only resolved once (use_cache=True)."""
    app = APIGatewayHttpResolver()
    call_count = 0

    def get_config() -> dict:
        nonlocal call_count
        call_count += 1
        return {"key": "value"}

    def get_a(config: Annotated[dict, Depends(get_config)]) -> str:
        return config["key"]

    def get_b(config: Annotated[dict, Depends(get_config)]) -> str:
        return config["key"]

    @app.post("/my/path")
    def handler(a: Annotated[str, Depends(get_a)], b: Annotated[str, Depends(get_b)]):
        return {"a": a, "b": b}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert call_count == 1  # get_config called once despite being used by both get_a and get_b


def test_depends_no_cache():
    """use_cache=False resolves every time."""
    app = APIGatewayHttpResolver()
    call_count = 0

    def get_value() -> int:
        nonlocal call_count
        call_count += 1
        return call_count

    @app.post("/my/path")
    def handler(
        a: Annotated[int, Depends(get_value, use_cache=False)],
        b: Annotated[int, Depends(get_value, use_cache=False)],
    ):
        return {"a": a, "b": b}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert call_count == 2


def test_depends_with_request():
    """A dependency can receive the Request object."""
    app = APIGatewayHttpResolver()

    def get_method(request: Request) -> str:
        return request.method

    @app.post("/my/path")
    def handler(method: Annotated[str, Depends(get_method)]):
        return {"method": method}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"method": "POST"}


def test_depends_override():
    """dependency_overrides replaces a dependency callable for testing."""
    app = APIGatewayHttpResolver()

    def get_tenant() -> str:
        return "real-tenant"

    @app.post("/my/path")
    def handler(tenant: Annotated[str, Depends(get_tenant)]):
        return {"tenant": tenant}

    app.dependency_overrides[get_tenant] = lambda: "test-tenant"

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"tenant": "test-tenant"}

    app.dependency_overrides.clear()


def test_depends_override_nested():
    """dependency_overrides works for nested dependencies too."""
    app = APIGatewayHttpResolver()

    def get_db_client():
        return "real-db"

    def get_table(db: Annotated[str, Depends(get_db_client)]) -> str:
        return f"table-from-{db}"

    @app.post("/my/path")
    def handler(table: Annotated[str, Depends(get_table)]):
        return {"table": table}

    app.dependency_overrides[get_db_client] = lambda: "mock-db"

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"table": "table-from-mock-db"}

    app.dependency_overrides.clear()


def test_depends_multiple_handlers():
    """Dependencies work across different route handlers."""
    app = APIGatewayHttpResolver()

    def get_user() -> str:
        return "user-123"

    @app.get("/my/path")
    def get_handler(user: Annotated[str, Depends(get_user)]):
        return {"user": user, "action": "get"}

    @app.post("/my/path")
    def post_handler(user: Annotated[str, Depends(get_user)]):
        return {"user": user, "action": "post"}

    # Test POST (matches the event)
    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"user": "user-123", "action": "post"}


def test_depends_reusable_type_alias():
    """Annotated type aliases can be reused across handlers."""
    app = APIGatewayHttpResolver()

    def get_tenant() -> str:
        return "tenant-abc"

    TenantId = Annotated[str, Depends(get_tenant)]

    @app.post("/my/path")
    def handler(tenant: TenantId):
        return {"tenant": tenant}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"tenant": "tenant-abc"}


def test_handler_without_depends_works_normally():
    """A plain handler with no Depends() params is not affected by DI."""
    app = APIGatewayHttpResolver()

    @app.post("/my/path")
    def handler():
        return {"ok": True}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"ok": True}


def test_depends_not_cached_across_invocations():
    """Each app() call resolves dependencies fresh — no cross-request leakage."""
    app = APIGatewayHttpResolver()
    call_count = 0

    def get_counter() -> int:
        nonlocal call_count
        call_count += 1
        return call_count

    @app.post("/my/path")
    def handler(c: Annotated[int, Depends(get_counter)]):
        return {"c": c}

    result1 = app(API_GW_V2_EVENT, {})
    result2 = app(API_GW_V2_EVENT, {})

    assert json.loads(result1["body"]) == {"c": 1}
    assert json.loads(result2["body"]) == {"c": 2}
    assert call_count == 2


def test_depends_deeply_nested():
    """Three-level dependency chain resolves correctly."""
    app = APIGatewayHttpResolver()

    def get_url() -> str:
        return "postgres://localhost"

    def get_conn(url: Annotated[str, Depends(get_url)]) -> str:
        return f"conn({url})"

    def get_session(conn: Annotated[str, Depends(get_conn)]) -> str:
        return f"session({conn})"

    @app.post("/my/path")
    def handler(session: Annotated[str, Depends(get_session)]):
        return {"session": session}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"session": "session(conn(postgres://localhost))"}


def test_depends_with_request_reads_headers():
    """A dependency using Request can read actual request headers."""
    app = APIGatewayHttpResolver()

    def get_user_agent(request: Request) -> str:
        return request.headers.get("user-agent", "unknown")

    @app.post("/my/path")
    def handler(ua: Annotated[str, Depends(get_user_agent)]):
        return {"ua": ua}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert isinstance(json.loads(result["body"])["ua"], str)


def test_depends_returning_none():
    """A dependency can return None without breaking."""
    app = APIGatewayHttpResolver()

    def get_nothing() -> None:
        return None

    @app.post("/my/path")
    def handler(val: Annotated[None, Depends(get_nothing)]):
        return {"val": val}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"val": None}


def test_depends_exception_raises_dependency_resolution_error():
    """If a dependency raises, a DependencyResolutionError wraps the original exception."""
    app = APIGatewayHttpResolver()

    def broken() -> str:
        raise ValueError("boom")

    @app.post("/my/path")
    def handler(val: Annotated[str, Depends(broken)]):
        return {"val": val}

    with pytest.raises(DependencyResolutionError, match="broken.*boom"):
        app(API_GW_V2_EVENT, {})


def test_depends_non_callable_raises_dependency_resolution_error():
    """Passing a non-callable to Depends() raises DependencyResolutionError immediately."""
    with pytest.raises(DependencyResolutionError, match="requires a callable"):
        Depends("not_a_function")  # type: ignore

    with pytest.raises(DependencyResolutionError, match="requires a callable"):
        Depends(42)  # type: ignore

    with pytest.raises(DependencyResolutionError, match="requires a callable"):
        Depends(None)  # type: ignore


def test_depends_accepts_lambda():
    """Depends() works with a lambda as the dependency."""
    app = APIGatewayHttpResolver()

    @app.post("/my/path")
    def handler(val: Annotated[str, Depends(lambda: "from-lambda")]):
        return {"val": val}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"val": "from-lambda"}


def test_depends_accepts_class_with_call():
    """Depends() works with a class that implements __call__."""
    app = APIGatewayHttpResolver()

    class TenantProvider:
        def __call__(self) -> str:
            return "tenant-from-class"

    @app.post("/my/path")
    def handler(tenant: Annotated[str, Depends(TenantProvider())]):
        return {"tenant": tenant}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"tenant": "tenant-from-class"}


def test_depends_accepts_class_as_factory():
    """Depends() works with a class itself (constructor as callable)."""
    app = APIGatewayHttpResolver()

    class Config:
        def __init__(self):
            self.region = "us-east-1"

    @app.post("/my/path")
    def handler(config: Annotated[Config, Depends(Config)]):
        return {"region": config.region}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"region": "us-east-1"}


def test_depends_with_unresolvable_annotations_is_ignored():
    """A handler whose annotations cannot be resolved by get_type_hints is treated as having no deps."""
    app = APIGatewayHttpResolver()

    # Build a function with broken annotations that get_type_hints cannot resolve.
    # The param has a default so the handler can still be called without it.
    def make_handler():
        def handler(x: "CompletelyBogusType" = None):  # noqa: F821
            return {"ok": True}

        return handler

    app.post("/my/path")(make_handler())

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"ok": True}


def test_depends_without_request_does_not_inject():
    """A dependency that does NOT declare Request still works when request is available."""
    app = APIGatewayHttpResolver()

    def get_static() -> str:
        return "no-request-needed"

    @app.post("/my/path")
    def handler(val: Annotated[str, Depends(get_static)]):
        return {"val": val}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"val": "no-request-needed"}


def test_depends_with_broken_type_hints_on_dependency():
    """A dependency callable with broken annotations still resolves (get_type_hints fails gracefully)."""
    app = APIGatewayHttpResolver()

    # Create a callable whose annotations reference a nonexistent type
    # so get_type_hints() will raise inside solve_dependencies
    broken_dep = type(
        "BrokenDep",
        (),
        {
            "__call__": lambda self: "it-works",
            "__annotations__": {"x": "NonExistentType"},
            "__module__": __name__,
        },
    )()

    @app.post("/my/path")
    def handler(val: Annotated[str, Depends(broken_dep)]):
        return {"val": val}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"val": "it-works"}


# ---------------------------------------------------------------------------
# request.context — bridge between middleware and Depends()
# ---------------------------------------------------------------------------


def test_depends_request_context_writable():
    """Dependencies can write to request.context and handlers can read it."""
    app = APIGatewayHttpResolver()

    def set_tenant(request: Request) -> str:
        tenant = request.headers.get("x-tenant-id", "default")
        request.context["tenant"] = tenant
        return tenant

    @app.post("/my/path")
    def handler(tenant: Annotated[str, Depends(set_tenant)], request: Request):
        return {"tenant": tenant, "from_context": request.context.get("tenant")}

    event = {**API_GW_V2_EVENT, "headers": {**API_GW_V2_EVENT.get("headers", {}), "x-tenant-id": "acme-corp"}}
    result = app(event, {})

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["tenant"] == "acme-corp"
    assert body["from_context"] == "acme-corp"


def test_depends_request_context_bridges_middleware():
    """Middleware writes to app.context, Depends() reads via request.context."""
    app = APIGatewayHttpResolver()

    def auth_middleware(app, next_middleware):
        app.append_context(user="admin-user")
        return next_middleware(app)

    app.use(middlewares=[auth_middleware])

    def get_current_user(request: Request) -> str:
        return request.context["user"]

    @app.post("/my/path")
    def handler(user: Annotated[str, Depends(get_current_user)]):
        return {"user": user}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"user": "admin-user"}


def test_depends_request_context_with_router():
    """request.context works when routes come from an included Router."""
    from aws_lambda_powertools.event_handler.api_gateway import Router

    app = APIGatewayHttpResolver()
    router = Router()

    def mw(app, next_middleware):
        app.append_context(role="admin")
        return next_middleware(app)

    app.use(middlewares=[mw])

    def get_role(request: Request) -> str:
        return request.context["role"]

    @router.post("/my/path")
    def handler(role: Annotated[str, Depends(get_role)]):
        return {"role": role}

    app.include_router(router)

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"role": "admin"}


def test_depends_request_resolved_event():
    """Dependencies can access the full event via request.resolved_event."""
    app = APIGatewayHttpResolver()

    def get_path(request: Request) -> str:
        return request.resolved_event.path

    @app.post("/my/path")
    def handler(path: Annotated[str, Depends(get_path)]):
        return {"path": path}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["path"] == "/my/path"


# ---------------------------------------------------------------------------
# Exceptions raised by dependencies are handled like exceptions raised by the route
# ---------------------------------------------------------------------------


def get_current_user() -> str:
    """Auth dependency rejecting a request without credentials, like the docs example."""
    raise UnauthorizedError("Missing authentication")


def test_depends_service_error_returns_its_status_code():
    """A ServiceError raised by a dependency returns its HTTP response, as if the route raised it."""
    app = APIGatewayHttpResolver()

    @app.post("/my/path")
    def handler(user: Annotated[str, Depends(get_current_user)]):
        return {"user": user}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 401
    assert json.loads(result["body"]) == {"statusCode": 401, "message": "Missing authentication"}


def test_depends_exception_handled_by_exception_handler():
    """An exception_handler receives the exception the dependency raised, not DependencyResolutionError."""
    app = APIGatewayHttpResolver()

    class TenantNotFoundError(Exception):
        pass

    @app.exception_handler(TenantNotFoundError)
    def handle_tenant_not_found(ex: TenantNotFoundError):
        return Response(status_code=404, content_type=content_types.TEXT_PLAIN, body=str(ex))

    def get_tenant() -> str:
        raise TenantNotFoundError("Tenant acme not found")

    @app.post("/my/path")
    def handler(tenant: Annotated[str, Depends(get_tenant)]):
        return {"tenant": tenant}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 404
    assert result["body"] == "Tenant acme not found"


def test_depends_nested_service_error_returns_its_status_code():
    """A ServiceError raised by a nested dependency returns its HTTP response."""
    app = APIGatewayHttpResolver()

    def get_tenant(user: Annotated[str, Depends(get_current_user)]) -> str:
        return f"tenant-of-{user}"

    @app.post("/my/path")
    def handler(tenant: Annotated[str, Depends(get_tenant)]):
        return {"tenant": tenant}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 401
    assert json.loads(result["body"]) == {"statusCode": 401, "message": "Missing authentication"}


def test_depends_dependency_resolution_error_handler_takes_precedence():
    """An exception_handler for DependencyResolutionError still receives it, with the original exception as cause."""
    app = APIGatewayHttpResolver()

    @app.exception_handler(DependencyResolutionError)
    def handle_dependency_error(ex: DependencyResolutionError):
        return Response(status_code=500, content_type=content_types.TEXT_PLAIN, body=type(ex.__cause__).__name__)

    @app.post("/my/path")
    def handler(user: Annotated[str, Depends(get_current_user)]):
        return {"user": user}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 500
    assert result["body"] == "UnauthorizedError"


def test_depends_service_error_returns_its_status_code_with_resolve_async():
    """resolve_async() also returns the HTTP response of a ServiceError raised by a dependency."""
    app = APIGatewayHttpResolver()

    @app.post("/my/path")
    async def handler(user: Annotated[str, Depends(get_current_user)]):
        return {"user": user}

    result = asyncio.run(app.resolve_async(API_GW_V2_EVENT, {}))
    assert result["statusCode"] == 401
    assert json.loads(result["body"]) == {"statusCode": 401, "message": "Missing authentication"}


def test_depends_exception_with_resolve_async_raises_dependency_resolution_error():
    """With resolve_async(), an exception that no handler handles still raises DependencyResolutionError."""
    app = APIGatewayHttpResolver()

    def broken() -> str:
        raise ValueError("boom")

    @app.post("/my/path")
    async def handler(val: Annotated[str, Depends(broken)]):
        return {"val": val}

    with pytest.raises(DependencyResolutionError, match="broken.*boom"):
        asyncio.run(app.resolve_async(API_GW_V2_EVENT, {}))


@pytest.mark.parametrize(
    "resolver, event_file, path",
    [
        pytest.param(APIGatewayRestResolver, "apiGatewayProxyEvent.json", "/my/path", id="rest-api"),
        pytest.param(APIGatewayHttpResolver, "apiGatewayProxyV2Event_GET.json", "/my/path", id="http-api"),
        pytest.param(ALBResolver, "albEvent.json", "/lambda", id="alb"),
        pytest.param(VPCLatticeV2Resolver, "vpcLatticeV2Event.json", "/newpath", id="vpc-lattice-v2"),
    ],
)
def test_depends_service_error_returns_its_status_code_for_each_resolver(resolver, event_file, path):
    """Each proxy resolver returns the HTTP response of a ServiceError raised by a dependency."""
    app = resolver()

    @app.get(path)
    def handler(user: Annotated[str, Depends(get_current_user)]):
        return {"user": user}

    result = app.resolve(load_event(event_file), {})
    assert result["statusCode"] == 401
    assert json.loads(result["body"]) == {"statusCode": 401, "message": "Missing authentication"}


def test_depends_class_dependency_receives_request():
    """A class dependency gets Request injected into its __init__."""
    app = APIGatewayHttpResolver()

    class Service:
        def __init__(self, request: Request):
            self.path = request.resolved_event.path

    @app.post("/my/path")
    def handler(svc: Annotated[Service, Depends(Service)]):
        return {"path": svc.path}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"path": "/my/path"}


def test_depends_class_dependency_with_nested_depends():
    """A class dependency resolves its own Depends() parameters declared on __init__."""
    app = APIGatewayHttpResolver()

    def get_tenant() -> str:
        return "tenant-1"

    class Service:
        def __init__(self, tenant: Annotated[str, Depends(get_tenant)]):
            self.tenant = tenant

    @app.post("/my/path")
    def handler(svc: Annotated[Service, Depends(Service)]):
        return {"tenant": svc.tenant}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"tenant": "tenant-1"}
def test_depends_with_none_default_is_resolved():
    """A Depends() parameter that also declares ``= None`` is still resolved (Python 3.10 wraps it in Optional)."""
    app = APIGatewayHttpResolver()

    def get_region() -> str:
        return "eu-west-1"

    @app.post("/my/path")
    def handler(region: Annotated[str, Depends(get_region)] = None):
        return {"region": region}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"region": "eu-west-1"}


def test_depends_inside_explicit_optional_is_resolved():
    """``Optional[Annotated[str, Depends(...)]]`` and ``Annotated[...] | None`` both resolve."""
    from typing import Optional

    app = APIGatewayHttpResolver()

    def get_region() -> str:
        return "eu-west-1"

    def get_zone() -> str:
        return "a"

    @app.post("/my/path")
    def handler(
        region: Optional[Annotated[str, Depends(get_region)]] = None,  # noqa: UP045
        zone: Annotated[str, Depends(get_zone)] | None = None,
    ):
        return {"region": region, "zone": zone}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"region": "eu-west-1", "zone": "a"}


def test_request_param_with_none_default_is_injected():
    """A ``request: Request = None`` parameter is injected on every Python version."""
    app = APIGatewayHttpResolver()

    @app.post("/my/path")
    def handler(request: Request = None):
        return {"method": request.method}

    result = app(API_GW_V2_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"method": "POST"}
