from __future__ import annotations

import asyncio
import base64
import inspect
import threading
import warnings
from typing import TYPE_CHECKING, Any, Callable
from urllib.parse import parse_qs

from aws_lambda_powertools.event_handler.api_gateway import (
    ApiGatewayResolver,
    BaseRouter,
    ProxyEventType,
    Response,
    Route,
)
from aws_lambda_powertools.shared.headers_serializer import BaseHeadersSerializer
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent

if TYPE_CHECKING:
    from aws_lambda_powertools.shared.cookies import Cookie


class HttpHeadersSerializer(BaseHeadersSerializer):
    """Headers serializer for native HTTP responses."""

    def serialize(self, headers: dict[str, str | list[str]], cookies: list[Cookie]) -> dict[str, Any]:
        """Serialize headers for HTTP response format."""
        combined_headers: dict[str, str] = {}
        for key, values in headers.items():
            if values is None:  # pragma: no cover
                continue
            if isinstance(values, str):
                combined_headers[key] = values
            else:
                combined_headers[key] = ", ".join(values)

        # Add cookies as Set-Cookie headers
        cookie_headers = [str(cookie) for cookie in cookies] if cookies else []

        return {"headers": combined_headers, "cookies": cookie_headers}


class HttpProxyEvent(BaseProxyEvent):
    """
    A proxy event that wraps native HTTP request data.

    This allows the same route handlers to work with both Lambda and native HTTP servers.
    """

    def __init__(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        body: str | bytes | None = None,
        query_string: str | None = None,
        path_parameters: dict[str, str] | None = None,
        request_context: dict[str, Any] | None = None,
    ):
        # Parse query string
        query_params: dict[str, str] = {}
        multi_query_params: dict[str, list[str]] = {}

        if query_string:
            parsed = parse_qs(query_string, keep_blank_values=True)
            multi_query_params = parsed
            query_params = {k: v[-1] for k, v in parsed.items()}

        # Normalize body to string
        body_str = None
        if body is not None:
            body_str = body.decode("utf-8") if isinstance(body, bytes) else body

        # Build the internal dict structure that BaseProxyEvent expects
        data = {
            "httpMethod": method.upper(),
            "path": path,
            "headers": headers or {},
            "body": body_str,
            "isBase64Encoded": False,
            "queryStringParameters": query_params,
            "multiValueQueryStringParameters": multi_query_params,
            "pathParameters": path_parameters or {},
            "requestContext": request_context
            or {
                "stage": "local",
                "requestId": "local-request-id",
                "http": {"method": method.upper(), "path": path},
            },
        }

        super().__init__(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> HttpProxyEvent:
        """Create HttpProxyEvent directly from a dict (used internally)."""
        instance = object.__new__(cls)
        BaseProxyEvent.__init__(instance, data)
        return instance

    @classmethod
    def from_asgi(cls, scope: dict[str, Any], body: bytes | None = None) -> HttpProxyEvent:
        """
        Create an HttpProxyEvent from an ASGI scope dict.

        Parameters
        ----------
        scope : dict
            ASGI scope dictionary
        body : bytes, optional
            Request body

        Returns
        -------
        HttpProxyEvent
            Event object compatible with Powertools resolvers
        """
        # Extract headers from ASGI format [(b"key", b"value"), ...]
        headers: dict[str, str] = {}
        for key, value in scope.get("headers", []):
            header_name = key.decode("utf-8").lower()
            header_value = value.decode("utf-8")
            # Handle duplicate headers by joining with comma
            if header_name in headers:
                headers[header_name] = f"{headers[header_name]}, {header_value}"
            else:
                headers[header_name] = header_value

        return cls(
            method=scope["method"],
            path=scope["path"],
            headers=headers,
            body=body,
            query_string=scope.get("query_string", b"").decode("utf-8"),
        )

    def header_serializer(self) -> BaseHeadersSerializer:
        """Return the HTTP headers serializer."""
        return HttpHeadersSerializer()

    @property
    def resolved_query_string_parameters(self) -> dict[str, list[str]]:
        """Return query parameters in the format expected by OpenAPI validation."""
        return self.multi_value_query_string_parameters

    @property
    def resolved_headers_field(self) -> dict[str, str]:
        """Return headers in the format expected by OpenAPI validation."""
        return self.headers


class MockLambdaContext:
    """Minimal Lambda context for HTTP adapter."""

    function_name = "http-resolver"
    memory_limit_in_mb = 128
    invoked_function_arn = "arn:aws:lambda:local:000000000000:function:http-resolver"
    aws_request_id = "local-request-id"
    log_group_name = "/aws/lambda/http-resolver"
    log_stream_name = "local"

    def get_remaining_time_in_millis(self) -> int:  # pragma: no cover
        return 300000  # 5 minutes


class HttpResolverLocal(ApiGatewayResolver):
    """
    ASGI-compatible HTTP resolver for local development and testing.

    This resolver is designed specifically for local development workflows.
    It allows you to run your Powertools application locally with any ASGI server
    (uvicorn, hypercorn, daphne, etc.) while maintaining full compatibility with Lambda.

    The same code works in both environments - locally via ASGI and in Lambda via the handler.

    Supports both sync and async route handlers.

    WARNING
    -------
    This is intended for local development and testing only.
    The API may change in future releases. Do not use in production environments.

    Example
    -------
    ```python
    from aws_lambda_powertools.event_handler import HttpResolverLocal

    app = HttpResolverLocal()

    @app.get("/hello/<name>")
    async def hello(name: str):
        # Async handler - can use await
        return {"message": f"Hello, {name}!"}

    @app.get("/sync")
    def sync_handler():
        # Sync handlers also work
        return {"sync": True}

    # Run locally with uvicorn:
    # uvicorn app:app --reload

    # Deploy to Lambda (sync only):
    # handler = app
    ```
    """

    def __init__(
        self,
        cors: Any = None,
        debug: bool | None = None,
        serializer: Callable[[dict], str] | None = None,
        strip_prefixes: list[str | Any] | None = None,
        enable_validation: bool = False,
    ):
        warnings.warn(
            "HttpResolverLocal is intended for local development and testing only. "
            "The API may change in future releases. Do not use in production environments.",
            stacklevel=2,
        )
        super().__init__(
            proxy_type=ProxyEventType.APIGatewayProxyEvent,  # Use REST API format internally
            cors=cors,
            debug=debug,
            serializer=serializer,
            strip_prefixes=strip_prefixes,
            enable_validation=enable_validation,
        )
        self._is_async_mode = False

    def _to_proxy_event(self, event: dict) -> BaseProxyEvent:
        """Convert event dict to HttpProxyEvent."""
        # Create HttpProxyEvent directly from the dict data
        # The dict already has queryStringParameters and multiValueQueryStringParameters
        return HttpProxyEvent._from_dict(event)

    def _get_base_path(self) -> str:
        """Return the base path for HTTP resolver (no stage prefix)."""
        return ""

    async def _resolve_async(self) -> dict:
        """Async version of resolve that supports async handlers."""
        method = self.current_event.http_method.upper()
        path = self._remove_prefix(self.current_event.path)

        registered_routes = self._static_routes + self._dynamic_routes

        for route in registered_routes:
            if method != route.method:
                continue
            match_results = route.rule.match(path)
            if match_results:
                self.append_context(_route=route, _path=path)
                route_keys = self._convert_matches_into_route_keys(match_results)
                return await self._call_route_async(route, route_keys)

        # Handle not found
        return await self._handle_not_found_async()

    async def _call_route_async(self, route: Route, route_arguments: dict[str, str]) -> dict:
        """Call route handler, supporting both sync and async handlers."""
        from aws_lambda_powertools.event_handler.api_gateway import ResponseBuilder

        try:
            self._reset_processed_stack()

            # Get the route args (may be modified by validation middleware)
            self.append_context(_route_args=route_arguments)

            # Run middleware chain (sync for now, handlers can be async)
            response = await self._run_middleware_chain_async(route)

            response_builder: ResponseBuilder = ResponseBuilder(
                response=response,
                serializer=self._serializer,
                route=route,
            )

            return response_builder.build(self.current_event, self._cors)

        except Exception as exc:
            exc_response_builder = self._call_exception_handler(exc, route)
            if exc_response_builder:
                return exc_response_builder.build(self.current_event, self._cors)
            raise

    async def _run_middleware_chain_async(self, route: Route) -> Response:
        """Run the middleware chain, awaiting async handlers."""
        # Build middleware list
        all_middlewares: list[Callable[..., Any]] = []

        # Determine if validation should be enabled for this route
        # If route has explicit enable_validation setting, use it; otherwise, use resolver's global setting
        route_validation_enabled = (
            route.enable_validation if route.enable_validation is not None else self._enable_validation
        )

        if route_validation_enabled and hasattr(self, "_request_validation_middleware"):
            all_middlewares.append(self._request_validation_middleware)

        all_middlewares.extend(self._router_middlewares + route.middlewares)

        if route_validation_enabled and hasattr(self, "_response_validation_middleware"):
            all_middlewares.append(self._response_validation_middleware)

        # Create the final handler that calls the route function
        async def final_handler(app):
            route_args = app.context.get("_route_args", {})
            result = route.func(**route_args)

            # Await if coroutine
            if inspect.iscoroutine(result):
                result = await result

            return self._to_response(result)

        # Build middleware chain from end to start
        next_handler = final_handler

        for middleware in reversed(all_middlewares):
            next_handler = self._wrap_middleware_async(middleware, next_handler)

        return await next_handler(self)

    def _wrap_middleware_async(self, middleware: Callable, next_handler: Callable) -> Callable:
        """Wrap a middleware to work in async context.

        For sync middlewares, we split execution into pre/post phases around the
        call to next(). The sync middleware runs its pre-processing (e.g. request
        validation), then we intercept the next() call, await the async handler,
        and resume the middleware with the real response so post-processing
        (e.g. response validation) sees the actual data.
        """

        async def wrapped(app):
            if inspect.iscoroutinefunction(middleware):
                return await middleware(app, next_handler)

            # We use an Event to coordinate: the sync middleware runs in a thread,
            # calls sync_next which signals us to resolve the async handler,
            # then waits for the real response.
            middleware_called_next = asyncio.Event()
            next_app_holder: list = []
            real_response_holder: list = []
            middleware_result_holder: list = []
            middleware_error_holder: list = []

            def sync_next(app):
                next_app_holder.append(app)
                middleware_called_next.set()
                # Block this thread until the real response is available
                event = threading.Event()
                next_app_holder.append(event)
                event.wait()
                return real_response_holder[0]

            def run_middleware():
                try:
                    result = middleware(app, sync_next)
                    middleware_result_holder.append(result)
                except Exception as e:
                    middleware_error_holder.append(e)

            thread = threading.Thread(target=run_middleware, daemon=True)
            thread.start()

            # Wait for the middleware to call next()
            await middleware_called_next.wait()

            # Now resolve the async next_handler
            real_response = await next_handler(next_app_holder[0])
            real_response_holder.append(real_response)

            # Signal the thread that the response is ready
            threading_event = next_app_holder[1]
            threading_event.set()

            # Wait for the middleware thread to finish
            thread.join()

            if middleware_error_holder:
                raise middleware_error_holder[0]

            return middleware_result_holder[0]

        return wrapped

    async def _handle_not_found_async(self) -> dict:
        """Handle 404 responses, using custom not_found handler if registered."""
        from http import HTTPStatus

        from aws_lambda_powertools.event_handler.api_gateway import ResponseBuilder
        from aws_lambda_powertools.event_handler.exceptions import NotFoundError

        # Check for custom not_found handler
        custom_not_found_handler = self.exception_handler_manager.lookup_exception_handler(NotFoundError)
        if custom_not_found_handler:
            response = custom_not_found_handler(NotFoundError())
        else:
            response = Response(
                status_code=HTTPStatus.NOT_FOUND.value,
                content_type="application/json",
                body={"statusCode": HTTPStatus.NOT_FOUND.value, "message": "Not found"},
            )

        response_builder: ResponseBuilder = ResponseBuilder(
            response=response,
            serializer=self._serializer,
            route=None,
        )

        return response_builder.build(self.current_event, self._cors)

    async def asgi_handler(self, scope: dict, receive: Callable, send: Callable) -> None:
        """
        ASGI interface - allows running with uvicorn/hypercorn/etc.

        Parameters
        ----------
        scope : dict
            ASGI connection scope
        receive : Callable
            ASGI receive function
        send : Callable
            ASGI send function
        """
        if scope["type"] == "lifespan":
            # Handle lifespan events (startup/shutdown)
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return

        if scope["type"] != "http":
            return

        # Read request body
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break

        # Convert ASGI scope to HttpProxyEvent
        event = HttpProxyEvent.from_asgi(scope, body)

        # Create mock Lambda context
        context: Any = MockLambdaContext()

        # Set up resolver state (similar to resolve())
        BaseRouter.current_event = self._to_proxy_event(event._data)
        BaseRouter.lambda_context = context

        self._is_async_mode = True

        try:
            # Use async resolve
            response = await self._resolve_async()
        finally:
            self._is_async_mode = False
            self.clear_context()

        # Send HTTP response
        await self._send_response(send, response)

    async def __call__(  # type: ignore[override]
        self,
        scope: dict,
        receive: Callable,
        send: Callable,
    ) -> None:
        """ASGI interface - allows running with uvicorn/hypercorn/etc."""
        await self.asgi_handler(scope, receive, send)

    async def _send_response(self, send: Callable, response: dict) -> None:
        """Send the response via ASGI."""
        status_code = response.get("statusCode", 200)
        headers = response.get("headers", {})
        cookies = response.get("cookies", [])
        body = response.get("body", "")
        is_base64 = response.get("isBase64Encoded", False)

        # Build headers list for ASGI
        header_list: list[tuple[bytes, bytes]] = []
        for key, value in headers.items():
            header_list.append((key.lower().encode(), str(value).encode()))

        # Add Set-Cookie headers
        for cookie in cookies:
            header_list.append((b"set-cookie", str(cookie).encode()))

        # Send response start
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": header_list,
            },
        )

        # Prepare body
        if is_base64:
            body_bytes = base64.b64decode(body)
        elif isinstance(body, str):
            body_bytes = body.encode("utf-8")
        else:  # pragma: no cover
            body_bytes = body

        # Send response body
        await send(
            {
                "type": "http.response.body",
                "body": body_bytes,
            },
        )
