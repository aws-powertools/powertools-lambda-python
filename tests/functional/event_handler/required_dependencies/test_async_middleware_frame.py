import asyncio

import pytest

from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import (
    ApiGatewayResolver,
    ProxyEventType,
    Response,
)
from aws_lambda_powertools.event_handler.middlewares import NextMiddleware
from aws_lambda_powertools.event_handler.middlewares.async_utils import AsyncMiddlewareFrame, wrap_middleware_async
from tests.functional.utils import load_event

API_REST_EVENT = load_event("apiGatewayProxyEvent.json")


def _make_app() -> ApiGatewayResolver:
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)
    app.current_event = app._to_proxy_event(API_REST_EVENT)
    app.lambda_context = {}
    return app


def test_sync_middleware_raising_before_next_does_not_deadlock():
    # GIVEN a sync middleware that raises before calling next()
    # This previously caused a deadlock because middleware_called_next was never set
    app = _make_app()

    class AuthError(Exception):
        pass

    def failing_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
        raise AuthError("denied")

    async def next_handler(app: ApiGatewayResolver):
        await asyncio.sleep(0)
        return Response(200, content_types.TEXT_HTML, "should not reach")

    frame = AsyncMiddlewareFrame(current_middleware=failing_middleware, next_middleware=next_handler)

    # WHEN calling the frame
    # THEN the exception propagates without deadlocking
    with pytest.raises(AuthError, match="denied"):
        asyncio.run(frame(app))


def test_wrap_middleware_async_sync_raising_before_next_does_not_deadlock():
    # GIVEN a sync middleware that raises before calling next(), using wrap_middleware_async
    # This exercises _run_sync_middleware_in_thread directly
    app = _make_app()

    class AuthError(Exception):
        pass

    def failing_middleware(app, next_middleware):
        raise AuthError("denied")

    async def next_handler(app):
        return Response(200, content_types.TEXT_HTML, "should not reach")

    wrapped = wrap_middleware_async(failing_middleware, next_handler)

    # WHEN calling the wrapped middleware
    # THEN the exception propagates without deadlocking
    with pytest.raises(AuthError, match="denied"):
        asyncio.run(wrapped(app))


def test_async_middleware_raising_before_next_propagates():
    # GIVEN an async middleware that raises before calling next()
    app = _make_app()

    class ValidationError(Exception):
        pass

    async def failing_middleware(app: ApiGatewayResolver, next_middleware: NextMiddleware):
        raise ValidationError("invalid request")

    async def next_handler(app: ApiGatewayResolver):
        await asyncio.sleep(0)
        return Response(200, content_types.TEXT_HTML, "should not reach")

    frame = AsyncMiddlewareFrame(current_middleware=failing_middleware, next_middleware=next_handler)

    # WHEN calling the frame
    # THEN the exception propagates
    with pytest.raises(ValidationError, match="invalid request"):
        asyncio.run(frame(app))
