import asyncio
import re
from typing import cast

import pytest
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import (
    APIGatewayHttpResolver,
    ApiGatewayResolver,
    APIGatewayRestResolver,
    BaseRouter,
    ProxyEventType,
    Response,
    Route,
)
from aws_lambda_powertools.event_handler.depends import Depends
from aws_lambda_powertools.event_handler.middlewares.async_utils import _registered_api_adapter_async
from aws_lambda_powertools.event_handler.request import Request
from tests.functional.utils import load_event

API_REST_EVENT = load_event("apiGatewayProxyEvent.json")
API_RESTV2_EVENT = load_event("apiGatewayProxyV2Event_GET.json")


def _setup_resolver_context(app: ApiGatewayResolver, event: dict) -> None:
    """Populate the resolver context the same way resolve() does, without calling the full chain."""
    BaseRouter.current_event = app._to_proxy_event(cast(dict, event))
    BaseRouter.lambda_context = {}


@pytest.mark.parametrize(
    "app, event",
    [
        (ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent), API_REST_EVENT),
        (APIGatewayRestResolver(), API_REST_EVENT),
        (APIGatewayHttpResolver(), API_RESTV2_EVENT),
    ],
)
def test_sync_handler_returns_response(app: ApiGatewayResolver, event):
    # GIVEN a sync route handler
    @app.get("/my/path")
    def get_lambda():
        return Response(200, content_types.TEXT_HTML, "sync response")

    # WHEN resolving the event through the normal chain
    result = app(event, {})

    # THEN the sync handler is called and returns correctly
    assert result["statusCode"] == 200
    assert result["body"] == "sync response"


@pytest.mark.parametrize(
    "app, event",
    [
        (ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent), API_REST_EVENT),
        (APIGatewayRestResolver(), API_REST_EVENT),
        (APIGatewayHttpResolver(), API_RESTV2_EVENT),
    ],
)
def test_async_handler_is_awaited(app: ApiGatewayResolver, event):
    # GIVEN an async route handler registered on the resolver
    @app.get("/my/path")
    async def get_lambda():
        return Response(200, content_types.TEXT_HTML, "async response")

    # WHEN populating context and calling the async adapter directly
    _setup_resolver_context(app, event)
    app.append_context(_route_args={})

    result = asyncio.run(
        _registered_api_adapter_async(app, get_lambda),
    )

    # THEN the async handler is awaited and returns correctly
    assert result.status_code == 200
    assert result.body == "async response"


@pytest.mark.parametrize(
    "app, event",
    [
        (ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent), API_REST_EVENT),
        (APIGatewayRestResolver(), API_REST_EVENT),
        (APIGatewayHttpResolver(), API_RESTV2_EVENT),
    ],
)
def test_sync_handler_through_adapter(app: ApiGatewayResolver, event):
    # GIVEN a sync route handler
    @app.get("/my/path")
    def get_lambda():
        return Response(200, content_types.TEXT_HTML, "sync via adapter")

    # WHEN calling _registered_api_adapter_async with a sync handler
    _setup_resolver_context(app, event)
    app.append_context(_route_args={})

    result = asyncio.run(
        _registered_api_adapter_async(app, get_lambda),
    )

    # THEN sync handler works through the async adapter without issue
    assert result.status_code == 200
    assert result.body == "sync via adapter"


@pytest.mark.parametrize(
    "app, event",
    [
        (ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent), API_REST_EVENT),
        (APIGatewayRestResolver(), API_REST_EVENT),
        (APIGatewayHttpResolver(), API_RESTV2_EVENT),
    ],
)
def test_adapter_passes_route_args_to_async_handler(app: ApiGatewayResolver, event):
    # GIVEN an async handler that expects route arguments
    async def get_lambda(name: str):
        return Response(200, content_types.TEXT_HTML, name)

    # WHEN route_args are set in the context
    _setup_resolver_context(app, event)
    app.append_context(_route_args={"name": "powertools"})

    result = asyncio.run(
        _registered_api_adapter_async(app, get_lambda),
    )

    # THEN the route args are passed to the handler
    assert result.status_code == 200
    assert result.body == "powertools"


@pytest.mark.parametrize(
    "app, event",
    [
        (ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent), API_REST_EVENT),
        (APIGatewayRestResolver(), API_REST_EVENT),
        (APIGatewayHttpResolver(), API_RESTV2_EVENT),
    ],
)
def test_adapter_passes_route_args_to_sync_handler(app: ApiGatewayResolver, event):
    # GIVEN a sync handler that expects route arguments
    def get_lambda(name: str):
        return Response(200, content_types.TEXT_HTML, name)

    # WHEN route_args are set in the context
    _setup_resolver_context(app, event)
    app.append_context(_route_args={"name": "powertools"})

    result = asyncio.run(
        _registered_api_adapter_async(app, get_lambda),
    )

    # THEN the route args are passed to the sync handler
    assert result.status_code == 200
    assert result.body == "powertools"


def test_adapter_converts_dict_response_from_async_handler():
    # GIVEN an async handler that returns a dict (not a Response object)
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)

    async def get_lambda():
        return {"message": "hello"}

    # WHEN calling through the async adapter
    _setup_resolver_context(app, API_REST_EVENT)
    app.append_context(_route_args={})

    result = asyncio.run(
        _registered_api_adapter_async(app, get_lambda),
    )

    # THEN _to_response normalizes the dict into a Response object
    assert result.status_code == 200
    assert result.body is not None


def test_adapter_converts_tuple_response_from_async_handler():
    # GIVEN an async handler that returns a (dict, status_code) tuple
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)

    async def get_lambda():
        return {"created": True}, 201

    # WHEN calling through the async adapter
    _setup_resolver_context(app, API_REST_EVENT)
    app.append_context(_route_args={})

    result = asyncio.run(
        _registered_api_adapter_async(app, get_lambda),
    )

    # THEN _to_response normalizes the tuple into a Response object
    assert result.status_code == 201


def test_adapter_with_no_route_in_context():
    # GIVEN a handler and no _route in context
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)

    async def get_lambda():
        return Response(200, content_types.TEXT_HTML, "no route")

    # WHEN _route is None in context (default)
    _setup_resolver_context(app, API_REST_EVENT)
    app.append_context(_route_args={})

    result = asyncio.run(
        _registered_api_adapter_async(app, get_lambda),
    )

    # THEN the adapter skips request injection and dependency resolution
    assert result.status_code == 200
    assert result.body == "no route"


def test_adapter_injects_request_param():
    # GIVEN an async handler that declares a Request parameter
    app = APIGatewayHttpResolver()

    async def get_lambda(request: Request):
        return Response(200, content_types.TEXT_HTML, request.method)

    # WHEN a Route is present in context with request_param_name not yet checked
    _setup_resolver_context(app, API_RESTV2_EVENT)
    route = Route(
        method="GET",
        path="/my/path",
        rule=re.compile(r"^/my/path$"),
        func=get_lambda,
        cors=False,
        compress=False,
    )
    app.append_context(_route=route, _route_args={})

    result = asyncio.run(
        _registered_api_adapter_async(app, get_lambda),
    )

    # THEN the Request object is injected and request_param_name is cached
    assert result.status_code == 200
    assert route.request_param_name_checked is True
    assert route.request_param_name == "request"


def test_adapter_uses_cached_request_param_name():
    # GIVEN a Route where request_param_name was already resolved
    app = APIGatewayHttpResolver()

    async def get_lambda(req: Request):
        return Response(200, content_types.TEXT_HTML, req.method)

    _setup_resolver_context(app, API_RESTV2_EVENT)
    route = Route(
        method="GET",
        path="/my/path",
        rule=re.compile(r"^/my/path$"),
        func=get_lambda,
        cors=False,
        compress=False,
    )
    route.request_param_name = "req"
    route.request_param_name_checked = True
    app.append_context(_route=route, _route_args={})

    # WHEN calling the adapter a second time (cache hit)
    result = asyncio.run(
        _registered_api_adapter_async(app, get_lambda),
    )

    # THEN it still injects the Request using the cached param name
    assert result.status_code == 200


def test_adapter_resolves_dependencies():
    # GIVEN an async handler with Depends() parameters
    app = APIGatewayHttpResolver()

    def get_greeting() -> str:
        return "hello"

    async def get_lambda(greeting: Annotated[str, Depends(get_greeting)]):
        return {"greeting": greeting}

    _setup_resolver_context(app, API_RESTV2_EVENT)
    route = Route(
        method="GET",
        path="/my/path",
        rule=re.compile(r"^/my/path$"),
        func=get_lambda,
        cors=False,
        compress=False,
    )
    app.append_context(_route=route, _route_args={})

    # WHEN calling the adapter
    result = asyncio.run(
        _registered_api_adapter_async(app, get_lambda),
    )

    # THEN dependencies are resolved and injected
    assert result.status_code == 200


def test_adapter_resolves_dependencies_with_sync_handler():
    # GIVEN a sync handler with Depends() parameters
    app = APIGatewayHttpResolver()

    def get_greeting() -> str:
        return "hello"

    def get_lambda(greeting: Annotated[str, Depends(get_greeting)]):
        return {"greeting": greeting}

    _setup_resolver_context(app, API_RESTV2_EVENT)
    route = Route(
        method="GET",
        path="/my/path",
        rule=re.compile(r"^/my/path$"),
        func=get_lambda,
        cors=False,
        compress=False,
    )
    app.append_context(_route=route, _route_args={})

    # WHEN calling the adapter with a sync handler that has dependencies
    result = asyncio.run(
        _registered_api_adapter_async(app, get_lambda),
    )

    # THEN dependencies are resolved and injected for sync handler too
    assert result.status_code == 200
