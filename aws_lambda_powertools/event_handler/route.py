import warnings
from re import Pattern
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union, cast

from pydantic.fields import ModelField
from pydantic.schema import TypeModelOrEnum, field_schema

from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler.api_gateway import logger
from aws_lambda_powertools.event_handler.openapi.params import Dependant, Param
from aws_lambda_powertools.event_handler.openapi.utils import get_flat_params


class MiddlewareFrame:
    """
    creates a Middle Stack Wrapper instance to be used as a "Frame" in the overall stack of
    middleware functions.  Each instance contains the current middleware and the next
    middleware function to be called in the stack.

    In this way the middleware stack is constructed in a recursive fashion, with each middleware
    calling the next as a simple function call.  The actual Python call-stack will contain
    each MiddlewareStackWrapper "Frame", meaning any Middleware function can cause the
    entire Middleware call chain to be exited early (short-circuited) by raising an exception
    or by simply returning early with a custom Response.  The decision to short-circuit the middleware
    chain is at the user's discretion but instantly available due to the Wrapped nature of the
    callable constructs in the Middleware stack and each Middleware function having complete control over
    whether the "Next" handler in the stack is called or not.

    Parameters
    ----------
    current_middleware : Callable
        The current middleware function to be called as a request is processed.
    next_middleware : Callable
        The next middleware in the middleware stack.
    """

    def __init__(
        self,
        current_middleware: Callable[..., Any],
        next_middleware: Callable[..., Any],
    ) -> None:
        self.current_middleware: Callable[..., Any] = current_middleware
        self.next_middleware: Callable[..., Any] = next_middleware
        self._next_middleware_name = next_middleware.__name__

    @property
    def __name__(self) -> str:  # noqa: A003
        """Current middleware name

        It ensures backward compatibility with view functions being callable. This
        improves debugging since we need both current and next middlewares/callable names.
        """
        return self.current_middleware.__name__

    def __str__(self) -> str:
        """Identify current middleware identity and call chain for debugging purposes."""
        middleware_name = self.__name__
        return f"[{middleware_name}] next call chain is {middleware_name} -> {self._next_middleware_name}"

    def __call__(self, app: "ApiGatewayResolver") -> Union[Dict, Tuple, Response]:
        """
        Call the middleware Frame to process the request.

        Parameters
        ----------
        app: BaseRouter
            The router instance

        Returns
        -------
        Union[Dict, Tuple, Response]
            (tech-debt for backward compatibility).  The response type should be a
            Response object in all cases excepting when the original API route handler
            is called which will return one of 3 outputs.

        """
        # Do debug printing and push processed stack frame AFTER calling middleware
        # else the stack frame text of `current calling next` is confusing.
        logger.debug("MiddlewareFrame: %s", self)
        app._push_processed_stack_frame(str(self))

        return self.current_middleware(app, self.next_middleware)


class Route:
    """Internally used Route Configuration"""

    def __init__(
        self,
        method: str,
        path: str,
        rule: Pattern,
        func: Callable,
        cors: bool,
        compress: bool,
        cache_control: Optional[str],
        middlewares: Optional[List[Callable[..., Response]]],
    ):
        """

        Parameters
        ----------

        method: str
            The HTTP method, example "GET"
        rule: Pattern
            The route rule, example "/my/path"
        path: str
            The path of the route
        func: Callable
            The route handler function
        cors: bool
            Whether or not to enable CORS for this route
        compress: bool
            Whether or not to enable gzip compression for this route
        cache_control: Optional[str]
            The cache control header value, example "max-age=3600"
        middlewares: Optional[List[Callable[..., Response]]]
            The list of route middlewares to be called in order.
        """
        self.method = method.upper()
        self.path = path
        self.rule = rule
        self.func = func
        self._middleware_stack = func
        self.cors = cors
        self.compress = compress
        self.cache_control = cache_control
        self.middlewares = middlewares or []
        self.operation_id = self.method.title() + self.func.__name__.title()

        # _middleware_stack_built is used to ensure the middleware stack is only built once.
        self._middleware_stack_built = False

    def __call__(
        self,
        router_middlewares: List[Callable],
        app: "ApiGatewayResolver",
        route_arguments: Dict[str, str],
    ) -> Union[Dict, Tuple, Response]:
        """Calling the Router class instance will trigger the following actions:
            1. If Route Middleware stack has not been built, build it
            2. Call the Route Middleware stack wrapping the original function
                handler with the app and route arguments.

        Parameters
        ----------
        router_middlewares: List[Callable]
            The list of Router Middlewares (assigned to ALL routes)
        app: "ApiGatewayResolver"
            The ApiGatewayResolver instance to pass into the middleware stack
        route_arguments: Dict[str, str]
            The route arguments to pass to the app function (extracted from the Api Gateway
            Lambda Message structure from AWS)

        Returns
        -------
        Union[Dict, Tuple, Response]
            API Response object in ALL cases, except when the original API route
            handler is called which may also return a Dict, Tuple, or Response.
        """

        # Save CPU cycles by building middleware stack once
        if not self._middleware_stack_built:
            self._build_middleware_stack(router_middlewares=router_middlewares)

        # If debug is turned on then output the middleware stack to the console
        if app._debug:
            print(f"\nProcessing Route:::{self.func.__name__} ({app.context['_path']})")
            # Collect ALL middleware for debug printing - include internal _registered_api_adapter
            all_middlewares = router_middlewares + self.middlewares + [_registered_api_adapter]
            print("\nMiddleware Stack:")
            print("=================")
            print("\n".join(getattr(item, "__name__", "Unknown") for item in all_middlewares))
            print("=================")

        # Add Route Arguments to app context
        app.append_context(_route_args=route_arguments)

        # Call the Middleware Wrapped _call_stack function handler with the app
        return self._middleware_stack(app)

    def _build_middleware_stack(self, router_middlewares: List[Callable[..., Any]]) -> None:
        """
        Builds the middleware stack for the handler by wrapping each
        handler in an instance of MiddlewareWrapper which is used to contain the state
        of each middleware step.

        Middleware is represented by a standard Python Callable construct.  Any Middleware
        handler wanting to short-circuit the middlware call chain can raise an exception
        to force the Python call stack created by the handler call-chain to naturally un-wind.

        This becomes a simple concept for developers to understand and reason with - no additional
        gymanstics other than plain old try ... except.

        Notes
        -----
        The Route Middleware stack is processed in reverse order. This is so the stack of
        middleware handlers is applied in the order of being added to the handler.
        """
        all_middlewares = router_middlewares + self.middlewares
        logger.debug(f"Building middleware stack: {all_middlewares}")

        # IMPORTANT:
        # this must be the last middleware in the stack (tech debt for backward
        # compatibility purposes)
        #
        # This adapter will:
        #   1. Call the registered API passing only the expected route arguments extracted from the path
        # and not the middleware.
        #   2. Adapt the response type of the route handler (Union[Dict, Tuple, Response])
        # and normalise into a Response object so middleware will always have a constant signature
        all_middlewares.append(_registered_api_adapter)

        # Wrap the original route handler function in the middleware handlers
        # using the MiddlewareWrapper class callable construct in reverse order to
        # ensure middleware is applied in the order the user defined.
        #
        # Start with the route function and wrap from last to the first Middleware handler.
        for handler in reversed(all_middlewares):
            self._middleware_stack = MiddlewareFrame(current_middleware=handler, next_middleware=self._middleware_stack)

        self._middleware_stack_built = True

    def _openapi_path(
        self,
        *,
        dependant: Dependant,
        operation_ids: Set[str],
        model_name_map: Dict[TypeModelOrEnum, str],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        path = {}
        definitions: Dict[str, Any] = {}

        operation = self._openapi_operation_metadata(operation_ids=operation_ids)
        parameters: List[Dict[str, Any]] = []
        all_route_params = get_flat_params(dependant)
        operation_params = self._openapi_operation_parameters(
            all_route_params=all_route_params,
            model_name_map=model_name_map,
        )

        parameters.extend(operation_params)
        if parameters:
            all_parameters = {(param["in"], param["name"]): param for param in parameters}
            required_parameters = {(param["in"], param["name"]): param for param in parameters if param.get("required")}
            all_parameters.update(required_parameters)
            operation["parameters"] = list(all_parameters.values())

        responses = operation.setdefault("responses", {})
        success_response = responses.setdefault("200", {})
        success_response["description"] = "Success"
        success_response["content"] = {"application/json": {"schema": {}}}
        json_response = success_response["content"].setdefault("application/json", {})

        json_response["schema"] = self._openapi_operation_return(
            operation_id=self.operation_id,
            param=dependant.return_param,
            model_name_map=model_name_map,
        )

        path[self.method.lower()] = operation

        # Generate the response schema
        return path, definitions

    def _openapi_operation_summary(self):
        # TODO: add name, summary to Route, and allow it to be customized during creation
        self.rule.__str__().replace("_", " ").title()

    def _openapi_operation_metadata(self, operation_ids: Set[str]) -> Dict[str, Any]:
        operation: Dict[str, Any] = {"summary": self._openapi_operation_summary()}

        # TODO: description, tags
        operation_id = self.operation_id
        if operation_id in operation_ids:
            message = f"Duplicate Operation ID {operation_id} for function {self.func.__name__}"
            file_name = getattr(self.func, "__globals__", {}).get("__file__")
            if file_name:
                message += f" in {file_name}"
            warnings.warn(message, stacklevel=1)
        operation_ids.add(operation_id)
        operation["operationId"] = operation_id
        return operation

    @staticmethod
    def _openapi_operation_parameters(
        *,
        all_route_params: Sequence[ModelField],
        model_name_map: Dict[TypeModelOrEnum, str],
    ) -> List[Dict[str, Any]]:
        parameters = []
        for param in all_route_params:
            field_info = param.field_info
            field_info = cast(Param, field_info)
            if not field_info.include_in_schema:
                continue

            param_schema = field_schema(param, model_name_map=model_name_map, ref_prefix="#/components/schemas/")[0]

            parameter = {
                "name": param.alias,
                "in": field_info.in_.value,
                "required": param.required,
                "schema": param_schema,
            }

            if field_info.description:
                parameter["description"] = field_info.description

            if field_info.deprecated:
                parameter["deprecated"] = field_info.deprecated

            parameters.append(parameter)

        return parameters

    @staticmethod
    def _openapi_operation_return(
        *,
        operation_id: str,
        param: Optional[ModelField],
        model_name_map: Dict[TypeModelOrEnum, str],
    ) -> Dict[str, Any]:
        if param is None:
            return {}

        return_schema = field_schema(
            param,
            model_name_map=model_name_map,
            ref_prefix="#/components/schemas/",
        )[0]

        return {"name": f"Return {operation_id}", "schema": return_schema}


def _registered_api_adapter(
    app: "ApiGatewayResolver",
    next_middleware: Callable[..., Any],
) -> Union[Dict, Tuple, Response]:
    """
    Calls the registered API using the "_route_args" from the Resolver context to ensure the last call
    in the chain will match the API route function signature and ensure that Powertools passes the API
    route handler the expected arguments.

    **IMPORTANT: This internal middleware ensures the actual API route is called with the correct call signature
    and it MUST be the final frame in the middleware stack.  This can only be removed when the API Route
    function accepts `app: BaseRouter` as the first argument - which is the breaking change.

    Parameters
    ----------
    app: ApiGatewayResolver
        The API Gateway resolver
    next_middleware: Callable[..., Any]
        The function to handle the API

    Returns
    -------
    Response
        The API Response Object

    """
    route_args: Dict = app.context.get("_route_args", {})
    logger.debug(f"Calling API Route Handler: {route_args}")

    return app._to_response(next_middleware(**route_args))
