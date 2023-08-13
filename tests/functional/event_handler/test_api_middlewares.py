from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import (
    ApiGatewayResolver,
    ProxyEventType,
    Response,
    Router,
)
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.event_handler.middlewares import SchemaValidationMiddleware
from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
)
from tests.functional.utils import load_event

LOAD_GW_EVENT = load_event("apiGatewayProxyEvent.json")


def test_route_with_middleware():
    # GIVEN a Rest API Gateway proxy type event
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)

    # define custom middleware to inject new argument - "custom"
    def middleware_1(app, get_response, **kwargs):
        # inject a variable into the kwargs
        response = get_response(app, custom="custom", **kwargs)

        return response

    # define custom middleware to inject new argument - "another_one"
    def middleware_2(app, get_response, **kwargs):
        # inject a variable into the kwargs
        response = get_response(app, another_one=6, **kwargs)

        return response

    @app.get("/my/path", middlewares=[middleware_1, middleware_2])
    def get_lambda(another_one: int, custom: str) -> Response:
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        assert another_one == 6
        assert custom == "custom"
        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.TEXT_HTML]
    assert result["body"] == "foo"


def test_with_router_middleware():
    # GIVEN a Rest API Gateway proxy type event
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)

    # define custom middleware to inject new argument - "custom"
    def middleware_1(app, get_response, **kwargs):
        # inject a variable into the kwargs
        response = get_response(app, custom="custom", **kwargs)

        return response

    # define custom middleware to inject new argument - "another_one"
    def middleware_2(app, get_response, **kwargs):
        # inject a variable into the kwargs
        response = get_response(app, another_one=6, **kwargs)

        return response

    app.use([middleware_1])

    @app.get("/my/path", middlewares=[middleware_2])
    def get_lambda(another_one: int, custom: str) -> Response:
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        assert another_one == 6
        assert custom == "custom"
        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.TEXT_HTML]
    assert result["body"] == "foo"


def test_dynamic_route_with_middleware():
    # GIVEN
    app = ApiGatewayResolver()

    def middleware_one(app, get_response, **kwargs):
        # inject a variable into the kwargs
        response = get_response(app, injected="injected_value", **kwargs)

        return response

    @app.get("/<name>/<my_id>", middlewares=[middleware_one])
    def get_lambda(my_id: str, name: str, injected: str) -> Response:
        assert name == "my"
        assert injected == "injected_value"

        return Response(200, content_types.TEXT_HTML, my_id)

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.TEXT_HTML]
    assert result["body"] == "path"


def test_middleware_early_return():
    # GIVEN
    app = ApiGatewayResolver()

    def middleware_one(app, get_response, **context):
        # inject a variable into the kwargs
        response = get_response(app, injected="injected_value", **context)

        return response

    def early_return_middleware(app, get_response, **context):
        assert context.get("injected") == "injected_value"

        return Response(400, content_types.TEXT_HTML, "bad_response")

    def not_executed_middleware(app, get_response, **context):
        # This should never be executed - if it is an excpetion will be raised
        raise NotImplementedError()

    @app.get("/<name>/<my_id>", middlewares=[middleware_one, early_return_middleware, not_executed_middleware])
    def get_lambda(my_id: str, name: str, injected: str) -> Response:
        assert name == "my"
        assert injected == "injected_value"

        return Response(200, content_types.TEXT_HTML, my_id)

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN
    assert result["statusCode"] == 400
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.TEXT_HTML]
    assert result["body"] == "bad_response"


def test_pass_schema_validation(validation_schema):
    # GIVEN
    app = ApiGatewayResolver()

    @app.post("/my/path", middlewares=[SchemaValidationMiddleware(validation_schema)])
    def post_lambda() -> Response:
        return Response(200, content_types.TEXT_HTML, "path")

    # WHEN calling the event handler
    result = app(load_event("apigatewayeSchemaMiddlwareValidEvent.json"), {})

    # THEN
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.TEXT_HTML]
    assert result["body"] == "path"


def test_fail_schema_validation(validation_schema):
    # GIVEN
    app = ApiGatewayResolver()

    @app.post("/my/path", middlewares=[SchemaValidationMiddleware(validation_schema)])
    def post_lambda() -> Response:
        return Response(200, content_types.TEXT_HTML, "Should not be returned")

    # WHEN calling the event handler
    result = app(load_event("apigatewayeSchemaMiddlwareInvalidEvent.json"), {})
    print(f"\nRESULT:::{result}")

    # THEN
    assert result["statusCode"] == 400
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    assert (
        result["body"]
        == "{\"statusCode\":400,\"message\":\"Bad Request: Failed schema validation. Error: data must contain ['message'] properties, Path: ['data'], Data: {'username': 'lessa'}\"}"  # noqa: E501
    )


def test_invalid_schema_validation():
    # GIVEN
    app = ApiGatewayResolver()

    @app.post("/my/path", middlewares=[SchemaValidationMiddleware(inbound_schema="schema.json")])
    def post_lambda() -> Response:
        return Response(200, content_types.TEXT_HTML, "Should not be returned")

    # WHEN calling the event handler
    result = app(load_event("apigatewayeSchemaMiddlwareValidEvent.json"), {})

    print(f"\nRESULT:::{result}")
    # THEN
    assert result["statusCode"] == 500
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    assert result["body"] == '{"statusCode":500,"message":"Internal Server Error"}'


def test_middleware_short_circuit_via_httperrors():
    # GIVEN
    app = ApiGatewayResolver()

    def middleware_one(app, get_response, **context):
        # inject a variable into the kwargs of the middleware chain
        response = get_response(app, injected="injected_value", **context)

        return response

    def early_return_middleware(app, get_response, **context):
        # ensure "injected" context variable is passed in by middleware_one
        assert context.get("injected") == "injected_value"
        raise BadRequestError("bad_response")

    def not_executed_middleware(app, get_response, **context):
        # This should never be executed - if it is an excpetion will be raised
        raise NotImplementedError()

    @app.get("/<name>/<my_id>", middlewares=[middleware_one, early_return_middleware, not_executed_middleware])
    def get_lambda(my_id: str, name: str, injected: str) -> Response:
        assert name == "my"
        assert injected == "injected_value"

        return Response(200, content_types.TEXT_HTML, my_id)

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN
    assert result["statusCode"] == 400
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    assert result["body"] == '{"statusCode":400,"message":"bad_response"}'


def test_api_gateway_app_router_with_middlewares():
    # GIVEN a Router with registered routes
    app = ApiGatewayResolver()
    router = Router()

    def app_middleware(app, get_response, **context):
        # inject a variable into the kwargs of the middleware chain
        response = get_response(app, app_injected="app_value", **context)

        return response

    app.use(middlewares=[app_middleware])

    def router_middleware(app, get_response, **context):
        # inject a variable into the kwargs of the middleware chain
        response = get_response(app, router_injected="router_value", **context)

        return response

    router.use(middlewares=[router_middleware])

    to_inject: str = "injected_value"

    def middleware_one(app, get_response, **context):
        # inject a variable into the kwargs of the middleware chain
        response = get_response(app, injected=to_inject, **context)

        return response

    @router.get("/my/path", middlewares=[middleware_one])
    def get_api_route(app_injected: str, router_injected: str, injected: str):
        # make sure value is injected by middleware_one
        assert injected == to_inject
        assert router_injected == "router_value"
        assert app_injected == "app_value"

        return Response(200, content_types.TEXT_HTML, injected)

    app.include_router(router)
    # WHEN calling the event handler after applying routes from router object
    result = app(LOAD_GW_EVENT, {})

    # THEN process event correctly
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.TEXT_HTML]
    assert result["body"] == to_inject
