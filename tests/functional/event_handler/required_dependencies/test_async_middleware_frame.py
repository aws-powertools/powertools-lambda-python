import asyncio

from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import (
    ApiGatewayResolver,
    ProxyEventType,
    Response,
)
from aws_lambda_powertools.event_handler.middlewares import NextMiddleware
from aws_lambda_powertools.event_handler.middlewares.async_utils import AsyncMiddlewareFrame
from tests.functional.utils import load_event

API_REST_EVENT = load_event("apiGatewayProxyEvent.json")


def _make_app() -> ApiGatewayResolver:
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)
    app.current_event = app._to_proxy_event(API_REST_EVENT)
    app.lambda_context = {}
    return app


class TestAsyncMiddlewareFrameWithAsyncMiddleware:
    def test_async_middleware_is_awaited(self):
        # GIVEN an async middleware and an async next handler
        app = _make_app()

        async def my_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
            app.append_context(middleware_called=True)
            return await next_middleware(app)

        async def next_handler(app: ApiGatewayResolver):
            await asyncio.sleep(0)
            return Response(200, content_types.TEXT_HTML, "from handler")

        frame = AsyncMiddlewareFrame(current_middleware=my_middleware, next_middleware=next_handler)

        # WHEN calling the frame
        result = asyncio.run(frame(app))

        # THEN the async middleware is invoked and the chain proceeds
        assert result.status_code == 200
        assert result.body == "from handler"
        assert app.context.get("middleware_called") is True

    def test_async_middleware_can_short_circuit(self):
        # GIVEN an async middleware that returns early without calling next
        app = _make_app()

        async def blocking_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
            await asyncio.sleep(0)
            return Response(403, content_types.TEXT_PLAIN, "forbidden")

        async def next_handler(app: ApiGatewayResolver):
            await asyncio.sleep(0)
            return Response(200, content_types.TEXT_HTML, "should not reach")

        frame = AsyncMiddlewareFrame(current_middleware=blocking_middleware, next_middleware=next_handler)

        # WHEN calling the frame
        result = asyncio.run(frame(app))

        # THEN the middleware short-circuits the chain
        assert result.status_code == 403
        assert result.body == "forbidden"

    def test_multiple_async_middlewares_chained(self):
        # GIVEN two async middlewares chained together
        app = _make_app()

        async def first_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
            app.append_context(first=True)
            return await next_middleware(app)

        async def second_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
            app.append_context(second=True)
            return await next_middleware(app)

        async def final_handler(app: ApiGatewayResolver):
            await asyncio.sleep(0)
            return Response(200, content_types.TEXT_HTML, "done")

        # WHEN building a chain: first -> second -> handler
        inner_frame = AsyncMiddlewareFrame(current_middleware=second_middleware, next_middleware=final_handler)
        outer_frame = AsyncMiddlewareFrame(current_middleware=first_middleware, next_middleware=inner_frame)

        result = asyncio.run(outer_frame(app))

        # THEN both middlewares run in order
        assert result.status_code == 200
        assert app.context.get("first") is True
        assert app.context.get("second") is True


class TestAsyncMiddlewareFrameWithSyncMiddleware:
    def test_sync_middleware_is_bridged(self):
        # GIVEN a sync middleware and an async next handler
        app = _make_app()

        def sync_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
            app.append_context(sync_called=True)
            return next_middleware(app)

        async def next_handler(app: ApiGatewayResolver):
            await asyncio.sleep(0)
            return Response(200, content_types.TEXT_HTML, "async handler")

        frame = AsyncMiddlewareFrame(current_middleware=sync_middleware, next_middleware=next_handler)

        # WHEN calling the frame
        result = asyncio.run(frame(app))

        # THEN the sync middleware is bridged via wrap_middleware_async
        assert result.status_code == 200
        assert result.body == "async handler"
        assert app.context.get("sync_called") is True

    def test_sync_middleware_can_short_circuit(self):
        # GIVEN a sync middleware that returns early
        app = _make_app()

        def sync_blocking(app: ApiGatewayResolver, next_middleware: NextMiddleware):
            return Response(401, content_types.TEXT_PLAIN, "unauthorized")

        async def next_handler(app: ApiGatewayResolver):
            await asyncio.sleep(0)
            return Response(200, content_types.TEXT_HTML, "should not reach")

        frame = AsyncMiddlewareFrame(current_middleware=sync_blocking, next_middleware=next_handler)

        # WHEN calling the frame
        result = asyncio.run(frame(app))

        # THEN the sync middleware short-circuits
        assert result.status_code == 401
        assert result.body == "unauthorized"


class TestAsyncMiddlewareFrameMixedChain:
    def test_sync_then_async_middleware(self):
        # GIVEN a chain with sync middleware followed by async middleware
        app = _make_app()

        def sync_mw(app: ApiGatewayResolver, next_middleware: NextMiddleware):
            app.append_context(sync_ran=True)
            return next_middleware(app)

        async def async_mw(app: ApiGatewayResolver, next_middleware: NextMiddleware):
            app.append_context(async_ran=True)
            return await next_middleware(app)

        async def handler(app: ApiGatewayResolver):
            await asyncio.sleep(0)
            return Response(200, content_types.TEXT_HTML, "mixed chain")

        inner = AsyncMiddlewareFrame(current_middleware=async_mw, next_middleware=handler)
        outer = AsyncMiddlewareFrame(current_middleware=sync_mw, next_middleware=inner)

        # WHEN calling the chain
        result = asyncio.run(outer(app))

        # THEN both middlewares execute in order
        assert result.status_code == 200
        assert app.context.get("sync_ran") is True
        assert app.context.get("async_ran") is True


class TestAsyncMiddlewareFrameProperties:
    def test_name_property(self):
        # GIVEN a middleware with a known name
        def my_named_middleware(app, next_mw):
            return next_mw(app)

        def next_handler(app):
            return Response(200, content_types.TEXT_HTML, "ok")

        frame = AsyncMiddlewareFrame(current_middleware=my_named_middleware, next_middleware=next_handler)

        # THEN __name__ returns the current middleware name
        assert frame.__name__ == "my_named_middleware"

    def test_str_representation(self):
        # GIVEN a frame with named middleware and next handler
        def auth_middleware(app, next_mw):
            return next_mw(app)

        def logging_middleware(app):
            return Response(200, content_types.TEXT_HTML, "ok")

        frame = AsyncMiddlewareFrame(current_middleware=auth_middleware, next_middleware=logging_middleware)

        # THEN str() shows the call chain
        assert str(frame) == "[auth_middleware] next call chain is auth_middleware -> logging_middleware"

    def test_pushes_processed_stack_frame(self):
        # GIVEN a frame
        app = _make_app()

        async def my_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
            return await next_middleware(app)

        async def handler(app: ApiGatewayResolver):
            await asyncio.sleep(0)
            return Response(200, content_types.TEXT_HTML, "ok")

        frame = AsyncMiddlewareFrame(current_middleware=my_middleware, next_middleware=handler)
        app._reset_processed_stack()

        # WHEN calling the frame
        asyncio.run(frame(app))

        # THEN the processed stack frame is recorded for debugging
        assert len(app.processed_stack_frames) > 0
        assert "my_middleware" in app.processed_stack_frames[0]
