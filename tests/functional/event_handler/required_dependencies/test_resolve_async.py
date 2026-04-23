import asyncio

import pytest

from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import (
    ALBResolver,
    APIGatewayHttpResolver,
    ApiGatewayResolver,
    APIGatewayRestResolver,
    BaseRouter,
    CORSConfig,
    ProxyEventType,
    Response,
)
from aws_lambda_powertools.event_handler.middlewares import NextMiddleware
from tests.functional.utils import load_event

API_REST_EVENT = load_event("apiGatewayProxyEvent.json")
API_RESTV2_EVENT = load_event("apiGatewayProxyV2Event_GET.json")
ALB_EVENT = load_event("albEvent.json")


def _setup_app(app, event):
    BaseRouter.current_event = app._to_proxy_event(event)
    BaseRouter.lambda_context = {}


RESOLVER_IDS = ["ApiGatewayResolver", "APIGatewayRestResolver", "APIGatewayHttpResolver", "ALBResolver"]


@pytest.fixture(
    params=[
        ("apigw_v1", API_REST_EVENT, "/my/path"),
        ("apigw_rest", API_REST_EVENT, "/my/path"),
        ("apigw_v2", API_RESTV2_EVENT, "/my/path"),
        ("alb", ALB_EVENT, "/lambda"),
    ],
    ids=RESOLVER_IDS,
)
def resolver_and_event(request):
    key, event, path = request.param
    resolvers = {
        "apigw_v1": ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent),
        "apigw_rest": APIGatewayRestResolver(),
        "apigw_v2": APIGatewayHttpResolver(),
        "alb": ALBResolver(),
    }
    return resolvers[key], event, path


class TestResolveAsyncWithAsyncHandlers:
    def test_async_handler_through_resolve_chain(self, resolver_and_event):
        # GIVEN an async handler registered on the resolver
        app, event, path = resolver_and_event

        @app.get(path)
        async def get_lambda():
            await asyncio.sleep(0)
            return Response(200, content_types.TEXT_HTML, "async works")

        # WHEN calling _resolve_async after setting up context
        _setup_app(app, event)
        result = asyncio.run(app._resolve_async())

        # THEN the async handler is awaited and returns a ResponseBuilder
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 200
        assert response["body"] == "async works"

    def test_async_handler_returning_dict(self, resolver_and_event):
        # GIVEN an async handler that returns a dict
        app, event, path = resolver_and_event

        @app.get(path)
        async def get_lambda():
            await asyncio.sleep(0)
            return {"message": "hello"}

        # WHEN calling _resolve_async
        _setup_app(app, event)
        result = asyncio.run(app._resolve_async())

        # THEN the dict is normalized into a Response
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 200

    def test_async_handler_returning_tuple(self, resolver_and_event):
        # GIVEN an async handler that returns a (dict, status_code) tuple
        app, event, path = resolver_and_event

        @app.get(path)
        async def get_lambda():
            await asyncio.sleep(0)
            return {"created": True}, 201

        # WHEN calling _resolve_async
        _setup_app(app, event)
        result = asyncio.run(app._resolve_async())

        # THEN the tuple is normalized with the correct status code
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 201


class TestResolveAsyncWithSyncHandlers:
    def test_sync_handler_works_through_async_chain(self, resolver_and_event):
        # GIVEN a sync handler
        app, event, path = resolver_and_event

        @app.get(path)
        def get_lambda():
            return Response(200, content_types.TEXT_HTML, "sync via async")

        # WHEN calling _resolve_async
        _setup_app(app, event)
        result = asyncio.run(app._resolve_async())

        # THEN the sync handler works through the async chain
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 200
        assert response["body"] == "sync via async"


class TestResolveAsyncRouteArguments:
    def test_route_args_passed_to_async_handler(self):
        # GIVEN an async handler with a path parameter
        app = APIGatewayHttpResolver()

        @app.get("/my/<name>")
        async def get_lambda(name: str):
            await asyncio.sleep(0)
            return Response(200, content_types.TEXT_HTML, name)

        # WHEN resolving a matching event
        event = load_event("apiGatewayProxyV2Event_GET.json")
        event["rawPath"] = "/my/powertools"
        event["requestContext"]["http"]["path"] = "/my/powertools"
        _setup_app(app, event)
        result = asyncio.run(app._resolve_async())

        # THEN route arguments are passed to the handler
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 200
        assert response["body"] == "powertools"


class TestResolveAsyncNotFound:
    def test_not_found_returns_404(self, resolver_and_event):
        # GIVEN no matching route
        app, event, _path = resolver_and_event

        @app.get("/other/path")
        async def get_lambda():
            await asyncio.sleep(0)
            return Response(200, content_types.TEXT_HTML, "should not reach")

        # WHEN resolving an event with a non-matching path
        _setup_app(app, event)
        result = asyncio.run(app._resolve_async())

        # THEN a 404 response is returned
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 404

    def test_custom_not_found_handler(self):
        # GIVEN a custom not_found handler
        app = APIGatewayRestResolver()

        @app.not_found
        def custom_not_found(exc):
            return Response(404, content_types.APPLICATION_JSON, '{"error": "custom 404"}')

        @app.get("/other")
        def get_lambda():
            return Response(200, content_types.TEXT_HTML, "not reached")

        # WHEN resolving with no matching route
        _setup_app(app, API_REST_EVENT)
        result = asyncio.run(app._resolve_async())

        # THEN the custom handler is called
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 404
        assert response["body"] == '{"error": "custom 404"}'

    def test_cors_preflight_returns_204(self):
        # GIVEN a resolver with CORS enabled
        app = APIGatewayRestResolver(cors=CORSConfig())

        @app.get("/my/path")
        def get_lambda():
            return Response(200, content_types.TEXT_HTML, "ok")

        # WHEN an OPTIONS request arrives for a non-matching path
        event = load_event("apiGatewayProxyEvent.json")
        event["httpMethod"] = "OPTIONS"
        _setup_app(app, event)
        result = asyncio.run(app._resolve_async())

        # THEN a 204 pre-flight response is returned
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 204


class TestResolveAsyncExceptionHandling:
    def test_exception_handler_catches_async_error(self):
        # GIVEN an async handler that raises and an exception handler
        app = APIGatewayRestResolver()

        @app.exception_handler(ValueError)
        def handle_value_error(exc):
            return Response(422, content_types.APPLICATION_JSON, '{"error": "validation failed"}')

        @app.get("/my/path")
        async def get_lambda():
            await asyncio.sleep(0)
            raise ValueError("bad input")

        # WHEN resolving
        _setup_app(app, API_REST_EVENT)
        result = asyncio.run(app._resolve_async())

        # THEN the exception handler catches the error
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 422


class TestResolveAsyncMiddleware:
    def test_sync_middleware_in_async_chain(self):
        # GIVEN a sync middleware
        app = APIGatewayRestResolver()

        def my_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
            app.append_context(sync_mw_called=True)
            return next_middleware(app)

        @app.get("/my/path", middlewares=[my_middleware])
        async def get_lambda():
            await asyncio.sleep(0)
            return Response(200, content_types.TEXT_HTML, "with middleware")

        # WHEN calling _resolve_async
        _setup_app(app, API_REST_EVENT)
        result = asyncio.run(app._resolve_async())

        # THEN the sync middleware runs in the async chain
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 200
        assert response["body"] == "with middleware"
        assert app.context.get("sync_mw_called") is True

    def test_async_middleware_in_async_chain(self):
        # GIVEN an async middleware
        app = APIGatewayRestResolver()

        async def my_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
            app.append_context(async_mw_called=True)
            return await next_middleware(app)

        @app.get("/my/path", middlewares=[my_middleware])
        async def get_lambda():
            await asyncio.sleep(0)
            return Response(200, content_types.TEXT_HTML, "async mw")

        # WHEN calling _resolve_async
        _setup_app(app, API_REST_EVENT)
        result = asyncio.run(app._resolve_async())

        # THEN the async middleware runs correctly
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 200
        assert app.context.get("async_mw_called") is True

    def test_not_found_goes_through_middleware(self):
        # GIVEN a global middleware
        middleware_called = []

        def tracking_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
            middleware_called.append(True)
            return next_middleware(app)

        app = APIGatewayRestResolver()
        app.use([tracking_middleware])

        @app.get("/other/path")
        def get_lambda():
            return Response(200, content_types.TEXT_HTML, "not reached")

        # WHEN resolving with a non-matching path
        _setup_app(app, API_REST_EVENT)
        result = asyncio.run(app._resolve_async())

        # THEN the middleware still runs (404 goes through chain)
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 404
        assert len(middleware_called) > 0


class TestResolveAsyncProcessedStack:
    def test_processed_stack_frames_recorded(self):
        # GIVEN an async handler
        app = APIGatewayRestResolver()

        @app.get("/my/path")
        async def get_lambda():
            await asyncio.sleep(0)
            return Response(200, content_types.TEXT_HTML, "ok")

        # WHEN calling _resolve_async
        _setup_app(app, API_REST_EVENT)
        asyncio.run(app._resolve_async())

        # THEN the processed stack frames are populated
        assert len(app.processed_stack_frames) > 0
        assert any("_registered_api_adapter_async" in frame for frame in app.processed_stack_frames)
