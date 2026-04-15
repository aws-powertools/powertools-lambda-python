"""Async middleware utilities for bridging sync and async middleware execution."""

from __future__ import annotations

import asyncio
import inspect
import threading
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, Response


def wrap_middleware_async(middleware: Callable, next_handler: Callable) -> Callable:
    """Wrap a middleware to work in an async context.

    For async middlewares, delegates directly with ``await``.

    For sync middlewares, runs the middleware in a background thread and uses
    ``asyncio.Event`` / ``threading.Event`` to coordinate the ``next()`` call
    so the async handler can be awaited on the main event-loop while the sync
    middleware blocks its own thread waiting for the result.

    Parameters
    ----------
    middleware : Callable
        A sync or async middleware ``(app, next_middleware) -> Response``.
    next_handler : Callable
        The next (async) handler in the chain.

    Returns
    -------
    Callable
        An async callable ``(app) -> Response`` that executes *middleware*
        followed by *next_handler*.
    """

    async def wrapped(app: ApiGatewayResolver) -> Response:
        if inspect.iscoroutinefunction(middleware):
            return await middleware(app, next_handler)

        return await _run_sync_middleware_in_thread(middleware, next_handler, app)

    return wrapped


async def _run_sync_middleware_in_thread(
    middleware: Callable,
    next_handler: Callable,
    app: Any,
) -> Any:
    """Execute a **sync** middleware inside a daemon thread.

    The sync middleware calls ``sync_next(app)`` which:

    1. Signals the async side that the middleware is ready for the next handler.
    2. Blocks the thread until the async handler has produced a response.
    3. Returns the response so the middleware can do post-processing.

    Meanwhile the async side awaits *next_handler*, feeds the response back,
    and waits for the thread to finish.
    """
    middleware_called_next = asyncio.Event()
    next_app_holder: list = []
    real_response_holder: list = []
    middleware_result_holder: list = []
    middleware_error_holder: list = []

    def sync_next(app: Any) -> Any:
        next_app_holder.append(app)
        middleware_called_next.set()
        # Block this thread until the async handler resolves
        event = threading.Event()
        next_app_holder.append(event)
        event.wait()
        return real_response_holder[0]

    def run_middleware() -> None:
        try:
            result = middleware(app, sync_next)
            middleware_result_holder.append(result)
        except Exception as e:
            middleware_error_holder.append(e)

    thread = threading.Thread(target=run_middleware, daemon=True)
    thread.start()

    # Wait for the middleware to call next()
    await middleware_called_next.wait()

    # Resolve the async next_handler on the event-loop
    real_response = await next_handler(next_app_holder[0])
    real_response_holder.append(real_response)

    # Unblock the middleware thread
    threading_event = next_app_holder[1]
    threading_event.set()

    # Wait for the middleware thread to complete post-processing
    thread.join()

    if middleware_error_holder:
        raise middleware_error_holder[0]

    return middleware_result_holder[0]
