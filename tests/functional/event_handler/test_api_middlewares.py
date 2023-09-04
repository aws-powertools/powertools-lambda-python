import pytest

from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import (
    APIGatewayHttpResolver,
    ApiGatewayResolver,
    APIGatewayRestResolver,
    BaseRouter,
    NextMiddlewareCallback,
    ProxyEventType,
    Response,
    Router,
)
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.event_handler.middlewares import BaseMiddlewareHandler, SchemaValidationMiddleware
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
def test_route_with_middleware(app: BaseRouter, event):
    # define custom middleware to inject new argument - "custom"
    def middleware_1(app: BaseRouter, next_middleware: NextMiddlewareCallback):
        # add additional data to Router Context
        app.append_context(custom="custom")
        response = next_middleware(app)

        return response

    # define custom middleware to inject new argument - "another_one"
    def middleware_2(app: BaseRouter, next_middleware: NextMiddlewareCallback):
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
def test_with_router_middleware(app: BaseRouter, event, other_event):
    # define custom middleware to inject new argument - "custom"
    def global_middleware(app: BaseRouter, next_middleware: NextMiddlewareCallback):
        # add custom data to context
        app.append_context(custom="custom")
        response = next_middleware(app)

        return response

    # define custom middleware to inject new argument - "another_one"
    def middleware_2(app: BaseRouter, next_middleware: NextMiddlewareCallback):
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
def test_dynamic_route_with_middleware(app: BaseRouter, event):
    def middleware_one(app: BaseRouter, next_middleware: NextMiddlewareCallback):
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
def test_middleware_early_return(app: BaseRouter, event):
    def middleware_one(app: BaseRouter, next_middleware):
        # inject a variable into resolver context
        app.append_context(injected="injected_value")
        response = next_middleware(app)

        return response

    def early_return_middleware(app: BaseRouter, next_middleware: NextMiddlewareCallback):
        assert app.context.get("injected") == "injected_value"

        return Response(400, content_types.TEXT_HTML, "bad_response")

    def not_executed_middleware(app: BaseRouter, next_middleware: NextMiddlewareCallback):
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
def test_pass_schema_validation(app: BaseRouter, event, validation_schema):
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
def test_fail_schema_validation(app: BaseRouter, event, validation_schema):
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
def test_invalid_schema_validation(app: BaseRouter, event):
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
def test_middleware_short_circuit_via_httperrors(app: BaseRouter, event):
    def middleware_one(app: BaseRouter, next_middleware: NextMiddlewareCallback):
        # inject a variable into the kwargs of the middleware chain
        app.append_context(injected="injected_value")
        response = next_middleware(app)

        return response

    def early_return_middleware(app: BaseRouter, next_middleware: NextMiddlewareCallback):
        # ensure "injected" context variable is passed in by middleware_one
        assert app.context.get("injected") == "injected_value"
        raise BadRequestError("bad_response")

    def not_executed_middleware(app: BaseRouter, next_middleware: NextMiddlewareCallback):
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
def test_api_gateway_app_router_with_middlewares(app: BaseRouter, event):
    # GIVEN a Router with registered routes
    router = Router()

    def app_middleware(app: BaseRouter, next_middleware):
        # inject a variable into the resolver context
        app.append_context(app_injected="app_value")
        response = next_middleware(app)

        return response

    app.use(middlewares=[app_middleware])

    def router_middleware(app: BaseRouter, next_middleware):
        # inject a variable into the resolver context
        app.append_context(router_injected="router_value")
        response = next_middleware(app)

        return response

    router.use(middlewares=[router_middleware])

    to_inject: str = "injected_value"

    def middleware_one(app: BaseRouter, next_middleware: NextMiddlewareCallback):
        # inject a variable into the kwargs of the middleware chain
        app.append_context(injected=to_inject)
        response = next_middleware(app)

        return response

    @router.get("/my/path", middlewares=[middleware_one])
    def get_api_route():
        # make sure value is injected by middleware_one
        injected: str = app.context.get("injected")
        assert injected == to_inject
        assert app.context.get("router_injected") == "router_value"
        assert app.context.get("app_injected") == "app_value"

        return Response(200, content_types.TEXT_HTML, injected)

    app.include_router(router)
    # WHEN calling the event handler after applying routes from router object
    result = app(event, {})

    # THEN process event correctly
    assert result["statusCode"] == 200
    assert result["body"] == to_inject


def test_class_based_middleware():
    # GIVEN a class-based middleware implementing BaseMiddlewareHandler correctly
    class CorrelationIdMiddleware(BaseMiddlewareHandler):
        def __init__(self, header: str):
            super().__init__()
            self.header = header

        def handler(self, app: ApiGatewayResolver, get_response: NextMiddlewareCallback, **kwargs) -> Response:
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
