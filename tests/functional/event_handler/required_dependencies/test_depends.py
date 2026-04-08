"""Tests for the Depends() dependency injection feature using Annotated."""

import json

import pytest
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.depends import DependencyResolutionError, Depends
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
