from typing import List

import pytest

from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import (
    APIGatewayHttpResolver,
    ApiGatewayResolver,
    APIGatewayRestResolver,
    ProxyEventType,
    Response,
    Router,
)
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.event_handler.middlewares import (
    BaseMiddlewareHandler,
    NextMiddleware,
)
from aws_lambda_powertools.event_handler.middlewares.schema_validation import (
    SchemaValidationMiddleware,
)
from aws_lambda_powertools.event_handler.types import EventHandlerInstance
from tests.functional.utils import load_event

API_REST_EVENT = load_event("apiGatewayProxyEvent.json")
API_RESTV2_EVENT = load_event("apiGatewayProxyV2Event_GET.json")


@pytest.mark.parametrize(
    "app, event",
    [
        (ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent), API_REST_EVENT),
        (APIGatewayRestResolver(), API_REST_EVENT),
        (APIGatewayHttpResolver(), API_RESTV2_EVENT),
    ],
)
def test_route_with_middleware(app: ApiGatewayResolver, event):
    # define custom middleware to inject new argument - "custom"
    def middleware_1(app: ApiGatewayResolver, next_middleware: NextMiddleware):
        # add additional data to Router Context
        app.append_context(custom="custom")
        response = next_middleware(app)

        return response

    # define custom middleware to inject new argument - "another_one"
    def middleware_2(app: ApiGatewayResolver, next_middleware: NextMiddleware):
        # add additional data to Router Context
        app.append_context(another_one=6)
        response = next_middleware(app)

        return response

    @app.get("/my/path", middlewares=[middleware_1, middleware_2])
    def get_lambda() -> Response:
        another_one = app.context.get("another_one")
        custom = app.context.get("custom")
        assert another_one == 6
        assert custom == "custom"

        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler
    result = app(event, {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result["body"] == "foo"


@pytest.mark.parametrize(
    "app, event, other_event",
    [
        (
            ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent),
            API_REST_EVENT,
            load_event("apiGatewayProxyOtherEvent.json"),
        ),
        (
            APIGatewayRestResolver(),
            API_REST_EVENT,
            load_event("apiGatewayProxyOtherEvent.json"),
        ),
        (
            APIGatewayHttpResolver(),
            API_RESTV2_EVENT,
            load_event("apiGatewayProxyV2OtherGetEvent.json"),
        ),
    ],
)
def test_with_router_middleware(app: ApiGatewayResolver, event, other_event):
    # define custom middleware to inject new argument - "custom"
    def global_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
        # add custom data to context
        app.append_context(custom="custom")
        response = next_middleware(app)

        return response

    # define custom middleware to inject new argument - "another_one"
    def middleware_2(app: ApiGatewayResolver, next_middleware: NextMiddleware):
        # add data to resolver context
        app.append_context(another_one=6)
        response = next_middleware(app)

        return response

    app.use([global_middleware])

    @app.get("/my/path", middlewares=[middleware_2])
    def get_lambda() -> Response:
        another_one: int = app.context.get("another_one")
        custom: str = app.context.get("custom")
        assert another_one == 6
        assert custom == "custom"

        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler
    result = app(event, {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result["body"] == "foo"

    @app.get("/other/path")
    def get_other_lambda() -> Response:
        custom: str = app.context.get("custom")
        assert custom == "custom"

        return Response(200, content_types.TEXT_HTML, "other_foo")

    # WHEN calling the event handler
    result = app(other_event, {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result["body"] == "other_foo"


@pytest.mark.parametrize(
    "app, event",
    [
        (ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent), API_REST_EVENT),
        (APIGatewayRestResolver(), API_REST_EVENT),
        (APIGatewayHttpResolver(), API_RESTV2_EVENT),
    ],
)
def test_dynamic_route_with_middleware(app: ApiGatewayResolver, event):
    def middleware_one(app: ApiGatewayResolver, next_middleware: NextMiddleware):
        # inject data into the resolver context
        app.append_context(injected="injected_value")
        response = next_middleware(app)

        return response

    @app.get("/<name>/<my_id>", middlewares=[middleware_one])
    def get_lambda(my_id: str, name: str) -> Response:
        injected: str = app.context.get("injected")
        assert name == "my"
        assert injected == "injected_value"

        return Response(200, content_types.TEXT_HTML, my_id)

    # WHEN calling the event handler
    result = app(event, {})

    # THEN
    assert result["statusCode"] == 200
    assert result["body"] == "path"


@pytest.mark.parametrize(
    "app, event",
    [
        (ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent), API_REST_EVENT),
        (APIGatewayRestResolver(), API_REST_EVENT),
        (APIGatewayHttpResolver(), API_RESTV2_EVENT),
    ],
)
def test_middleware_early_return(app: ApiGatewayResolver, event):
    def middleware_one(app: ApiGatewayResolver, next_middleware):
        # inject a variable into resolver context
        app.append_context(injected="injected_value")
        response = next_middleware(app)

        return response

    def early_return_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
        assert app.context.get("injected") == "injected_value"

        return Response(400, content_types.TEXT_HTML, "bad_response")

    def not_executed_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
        # This should never be executed - if it is an excpetion will be raised
        raise NotImplementedError()

    @app.get("/<name>/<my_id>", middlewares=[middleware_one, early_return_middleware, not_executed_middleware])
    def get_lambda(my_id: str, name: str) -> Response:
        assert name == "my"
        assert app.context.get("injected") == "injected_value"

        return Response(200, content_types.TEXT_HTML, my_id)

    # WHEN calling the event handler
    result = app(event, {})

    # THEN
    assert result["statusCode"] == 400
    assert result["body"] == "bad_response"


@pytest.mark.parametrize(
    "app, event",
    [
        (
            ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent),
            load_event("apigatewayeSchemaMiddlwareValidEvent.json"),
        ),
        (
            APIGatewayRestResolver(),
            load_event("apigatewayeSchemaMiddlwareValidEvent.json"),
        ),
        (
            APIGatewayHttpResolver(),
            load_event("apiGatewayProxyV2SchemaMiddlwareValidEvent.json"),
        ),
    ],
)
def test_pass_schema_validation(app: ApiGatewayResolver, event, validation_schema):
    @app.post("/my/path", middlewares=[SchemaValidationMiddleware(validation_schema)])
    def post_lambda() -> Response:
        return Response(200, content_types.TEXT_HTML, "path")

    # WHEN calling the event handler
    result = app(event, {})

    # THEN
    assert result["statusCode"] == 200
    assert result["body"] == "path"


@pytest.mark.parametrize(
    "app, event",
    [
        (
            ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent),
            load_event("apigatewayeSchemaMiddlwareInvalidEvent.json"),
        ),
        (
            APIGatewayRestResolver(),
            load_event("apigatewayeSchemaMiddlwareInvalidEvent.json"),
        ),
        (
            APIGatewayHttpResolver(),
            load_event("apiGatewayProxyV2SchemaMiddlwareInvalidEvent.json"),
        ),
    ],
)
def test_fail_schema_validation(app: ApiGatewayResolver, event, validation_schema):
    @app.post("/my/path", middlewares=[SchemaValidationMiddleware(validation_schema)])
    def post_lambda() -> Response:
        return Response(200, content_types.TEXT_HTML, "Should not be returned")

    # WHEN calling the event handler
    result = app(event, {})
    print(f"\nRESULT:::{result}")

    # THEN
    assert result["statusCode"] == 400
    assert (
        result["body"]
        == "{\"statusCode\":400,\"message\":\"Bad Request: Failed schema validation. Error: data must contain ['message'] properties, Path: ['data'], Data: {'username': 'lessa'}\"}"  # noqa: E501
    )


@pytest.mark.parametrize(
    "app, event",
    [
        (
            ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent),
            load_event("apigatewayeSchemaMiddlwareValidEvent.json"),
        ),
        (
            APIGatewayRestResolver(),
            load_event("apigatewayeSchemaMiddlwareValidEvent.json"),
        ),
        (
            APIGatewayHttpResolver(),
            load_event("apiGatewayProxyV2SchemaMiddlwareInvalidEvent.json"),
        ),
    ],
)
def test_invalid_schema_validation(app: ApiGatewayResolver, event):
    @app.post("/my/path", middlewares=[SchemaValidationMiddleware(inbound_schema="schema.json")])
    def post_lambda() -> Response:
        return Response(200, content_types.TEXT_HTML, "Should not be returned")

    # WHEN calling the event handler
    result = app(event, {})

    print(f"\nRESULT:::{result}")
    # THEN
    assert result["statusCode"] == 500
    assert result["body"] == '{"statusCode":500,"message":"Internal Server Error"}'


@pytest.mark.parametrize(
    "app, event",
    [
        (ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent), API_REST_EVENT),
        (APIGatewayRestResolver(), API_REST_EVENT),
        (APIGatewayHttpResolver(), API_RESTV2_EVENT),
    ],
)
def test_middleware_short_circuit_via_httperrors(app: ApiGatewayResolver, event):
    def middleware_one(app: ApiGatewayResolver, next_middleware: NextMiddleware):
        # inject a variable into the kwargs of the middleware chain
        app.append_context(injected="injected_value")
        response = next_middleware(app)

        return response

    def early_return_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
        # ensure "injected" context variable is passed in by middleware_one
        assert app.context.get("injected") == "injected_value"
        raise BadRequestError("bad_response")

    def not_executed_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
        # This should never be executed - if it is an excpetion will be raised
        raise NotImplementedError()

    @app.get("/<name>/<my_id>", middlewares=[middleware_one, early_return_middleware, not_executed_middleware])
    def get_lambda(my_id: str, name: str) -> Response:
        assert name == "my"
        assert app.context.get("injected") == "injected_value"

        return Response(200, content_types.TEXT_HTML, my_id)

    # WHEN calling the event handler
    result = app(event, {})

    # THEN
    assert result["statusCode"] == 400
    assert result["body"] == '{"statusCode":400,"message":"bad_response"}'


@pytest.mark.parametrize(
    "app, event",
    [
        (ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent), API_REST_EVENT),
        (APIGatewayRestResolver(), API_REST_EVENT),
        (APIGatewayHttpResolver(), API_RESTV2_EVENT),
    ],
)
def test_api_gateway_middleware_order_with_include_router_last(app: EventHandlerInstance, event):
    # GIVEN two global middlewares: one for App and one for Router
    router = Router()

    def global_app_middleware(app: EventHandlerInstance, next_middleware: NextMiddleware):
        middleware_order: List[str] = router.context.get("middleware_order", [])
        middleware_order.append("app")

        app.append_context(middleware_order=middleware_order)
        return next_middleware(app)

    def global_router_middleware(router: EventHandlerInstance, next_middleware: NextMiddleware):
        middleware_order: List[str] = router.context.get("middleware_order", [])
        middleware_order.append("router")

        router.append_context(middleware_order=middleware_order)
        return next_middleware(app)

    @router.get("/my/path")
    def dummy_route():
        middleware_order = app.context["middleware_order"]

        assert middleware_order[0] == "app"
        assert middleware_order[1] == "router"

        return Response(status_code=200, body="works!")

    # WHEN App global middlewares are registered first
    # followed by include_router

    router.use([global_router_middleware])  # mimics App importing Router
    app.use([global_app_middleware])
    app.include_router(router)

    # THEN resolving a request should start processing global Router middlewares first
    # due to insertion order
    result = app(event, {})

    assert result["statusCode"] == 200


@pytest.mark.parametrize(
    "app, event",
    [
        (ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent), API_REST_EVENT),
        (APIGatewayRestResolver(), API_REST_EVENT),
        (APIGatewayHttpResolver(), API_RESTV2_EVENT),
    ],
)
def test_api_gateway_middleware_order_with_include_router_first(app: EventHandlerInstance, event):
    # GIVEN two global middlewares: one for App and one for Router
    router = Router()

    def global_app_middleware(app: EventHandlerInstance, next_middleware: NextMiddleware):
        middleware_order: List[str] = router.context.get("middleware_order", [])
        middleware_order.append("app")

        app.append_context(middleware_order=middleware_order)
        return next_middleware(app)

    def global_router_middleware(router: EventHandlerInstance, next_middleware: NextMiddleware):
        middleware_order: List[str] = router.context.get("middleware_order", [])
        middleware_order.append("router")

        router.append_context(middleware_order=middleware_order)
        return next_middleware(app)

    @router.get("/my/path")
    def dummy_route():
        middleware_order = app.context["middleware_order"]

        assert middleware_order[0] == "router"
        assert middleware_order[1] == "app"

        return Response(status_code=200, body="works!")

    # WHEN App include router middlewares first
    # followed by App global middlewares registration

    router.use([global_router_middleware])  # mimics App importing Router
    app.include_router(router)

    app.use([global_app_middleware])

    # THEN resolving a request should start processing global Router middlewares first
    # due to insertion order
    result = app(event, {})

    assert result["statusCode"] == 200


def test_class_based_middleware():
    # GIVEN a class-based middleware implementing BaseMiddlewareHandler correctly
    class CorrelationIdMiddleware(BaseMiddlewareHandler):
        def __init__(self, header: str):
            super().__init__()
            self.header = header

        def handler(self, app: ApiGatewayResolver, get_response: NextMiddleware, **kwargs) -> Response:
            request_id = app.current_event.request_context.request_id  # type: ignore[attr-defined] # using REST event in a base Resolver # noqa: E501
            correlation_id = app.current_event.get_header_value(
                name=self.header,
                default_value=request_id,
            )  # noqa: E501

            response = get_response(app, **kwargs)
            response.headers[self.header] = correlation_id

            return response

    resolver = ApiGatewayResolver()
    event = load_event("apiGatewayProxyEvent.json")

    # WHEN instantiated with extra configuration as part of a route handler
    @resolver.get("/my/path", middlewares=[CorrelationIdMiddleware(header="X-Correlation-Id")])
    def post_lambda():
        return {"hello": "world"}

    # THEN it should work as any other middleware when a request is processed
    result = resolver(event, {})
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["X-Correlation-Id"][0] == resolver.current_event.request_context.request_id  # type: ignore[attr-defined] # noqa: E501
