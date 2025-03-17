from __future__ import annotations

import base64
import json
import logging
import re
import traceback
import warnings
import zlib
from abc import ABC, abstractmethod
from enum import Enum
from functools import partial
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, Mapping, Match, Pattern, Sequence, TypeVar, cast

from typing_extensions import override

from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.exceptions import NotFoundError, ServiceError
from aws_lambda_powertools.event_handler.openapi.config import OpenAPIConfig
from aws_lambda_powertools.event_handler.openapi.constants import (
    DEFAULT_API_VERSION,
    DEFAULT_OPENAPI_TITLE,
    DEFAULT_OPENAPI_VERSION,
)
from aws_lambda_powertools.event_handler.openapi.exceptions import (
    RequestValidationError,
    ResponseValidationError,
    SchemaValidationError,
)
from aws_lambda_powertools.event_handler.openapi.types import (
    COMPONENT_REF_PREFIX,
    METHODS_WITH_BODY,
    OpenAPIResponse,
    OpenAPIResponseContentModel,
    OpenAPIResponseContentSchema,
    validation_error_definition,
    validation_error_response_definition,
)
from aws_lambda_powertools.event_handler.util import (
    _FrozenDict,
    _FrozenListDict,
    _validate_openapi_security_parameters,
    extract_origin_header,
)
from aws_lambda_powertools.shared.cookies import Cookie
from aws_lambda_powertools.shared.functions import powertools_dev_is_set
from aws_lambda_powertools.shared.json_encoder import Encoder
from aws_lambda_powertools.utilities.data_classes import (
    ALBEvent,
    APIGatewayProxyEvent,
    APIGatewayProxyEventV2,
    BedrockAgentEvent,
    LambdaFunctionUrlEvent,
    VPCLatticeEvent,
    VPCLatticeEventV2,
)
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent

logger = logging.getLogger(__name__)

_DYNAMIC_ROUTE_PATTERN = r"(<\w+>)"
_SAFE_URI = "-._~()'!*:@,;=+&$"  # https://www.ietf.org/rfc/rfc3986.txt
# API GW/ALB decode non-safe URI chars; we must support them too
_UNSAFE_URI = r"%<> \[\]{}|^"
_NAMED_GROUP_BOUNDARY_PATTERN = rf"(?P\1[{_SAFE_URI}{_UNSAFE_URI}\\w]+)"
_DEFAULT_OPENAPI_RESPONSE_DESCRIPTION = "Successful Response"
_ROUTE_REGEX = "^{}$"

ResponseEventT = TypeVar("ResponseEventT", bound=BaseProxyEvent)
ResponseT = TypeVar("ResponseT")

if TYPE_CHECKING:
    from aws_lambda_powertools.event_handler.openapi.compat import (
        JsonSchemaValue,
        ModelField,
    )
    from aws_lambda_powertools.event_handler.openapi.models import (
        Contact,
        License,
        OpenAPI,
        SecurityScheme,
        Server,
        Tag,
    )
    from aws_lambda_powertools.event_handler.openapi.params import Dependant
    from aws_lambda_powertools.event_handler.openapi.swagger_ui.oauth2 import (
        OAuth2Config,
    )
    from aws_lambda_powertools.event_handler.openapi.types import (
        TypeModelOrEnum,
    )
    from aws_lambda_powertools.shared.cookies import Cookie
    from aws_lambda_powertools.shared.types import AnyCallableT
    from aws_lambda_powertools.utilities.typing import LambdaContext


class ProxyEventType(Enum):
    """An enumerations of the supported proxy event types."""

    APIGatewayProxyEvent = "APIGatewayProxyEvent"
    APIGatewayProxyEventV2 = "APIGatewayProxyEventV2"
    ALBEvent = "ALBEvent"
    BedrockAgentEvent = "BedrockAgentEvent"
    VPCLatticeEvent = "VPCLatticeEvent"
    VPCLatticeEventV2 = "VPCLatticeEventV2"
    LambdaFunctionUrlEvent = "LambdaFunctionUrlEvent"


class CORSConfig:
    """CORS Config

    Examples
    --------

    Simple CORS example using the default permissive CORS, note that this should only be used during early prototyping.

    ```python
    from aws_lambda_powertools.event_handler.api_gateway import (
        APIGatewayRestResolver, CORSConfig
    )

    app = APIGatewayRestResolver(cors=CORSConfig())

    @app.get("/my/path")
    def with_cors():
        return {"message": "Foo"}
    ```

    Using a custom CORSConfig where `with_cors` used the custom provided CORSConfig and `without_cors`
    do not include any CORS headers.

    ```python
    from aws_lambda_powertools.event_handler.api_gateway import (
        APIGatewayRestResolver, CORSConfig
    )

    cors_config = CORSConfig(
        allow_origin="https://wwww.example.com/",
        extra_origins=["https://dev.example.com/"],
        expose_headers=["x-exposed-response-header"],
        allow_headers=["x-custom-request-header"],
        max_age=100,
        allow_credentials=True,
    )
    app = APIGatewayRestResolver(cors=cors_config)

    @app.get("/my/path")
    def with_cors():
        return {"message": "Foo"}

    @app.get("/another-one", cors=False)
    def without_cors():
        return {"message": "Foo"}
    ```
    """

    _REQUIRED_HEADERS = ["Authorization", "Content-Type", "X-Amz-Date", "X-Api-Key", "X-Amz-Security-Token"]

    def __init__(
        self,
        allow_origin: str = "*",
        extra_origins: list[str] | None = None,
        allow_headers: list[str] | None = None,
        expose_headers: list[str] | None = None,
        max_age: int | None = None,
        allow_credentials: bool = False,
    ):
        """
        Parameters
        ----------
        allow_origin: str
            The value of the `Access-Control-Allow-Origin` to send in the response. Defaults to "*", but should
            only be used during development.
        extra_origins: list[str] | None
            The list of additional allowed origins.
        allow_headers: list[str] | None
            The list of additional allowed headers. This list is added to list of
            built-in allowed headers: `Authorization`, `Content-Type`, `X-Amz-Date`,
            `X-Api-Key`, `X-Amz-Security-Token`.
        expose_headers: list[str] | None
            A list of values to return for the Access-Control-Expose-Headers
        max_age: int | None
            The value for the `Access-Control-Max-Age`
        allow_credentials: bool
            A boolean value that sets the value of `Access-Control-Allow-Credentials`
        """

        self._allowed_origins = [allow_origin]

        if extra_origins:
            self._allowed_origins.extend(extra_origins)

        self.allow_headers = set(self._REQUIRED_HEADERS + (allow_headers or []))
        self.expose_headers = expose_headers or []
        self.max_age = max_age
        self.allow_credentials = allow_credentials

    def to_dict(self, origin: str | None) -> dict[str, str]:
        """Builds the configured Access-Control http headers"""

        # If there's no Origin, don't add any CORS headers
        if not origin:
            return {}

        # If the origin doesn't match any of the allowed origins, and we don't allow all origins ("*"),
        # don't add any CORS headers
        if origin not in self._allowed_origins and "*" not in self._allowed_origins:
            return {}

        # The origin matched an allowed origin, so return the CORS headers
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Headers": CORSConfig.build_allow_methods(self.allow_headers),
        }

        if self.expose_headers:
            headers["Access-Control-Expose-Headers"] = ",".join(self.expose_headers)
        if self.max_age is not None:
            headers["Access-Control-Max-Age"] = str(self.max_age)
        if origin != "*" and self.allow_credentials is True:
            headers["Access-Control-Allow-Credentials"] = "true"
        return headers

    def allowed_origin(self, extracted_origin: str) -> str | None:
        if extracted_origin in self._allowed_origins:
            return extracted_origin
        if extracted_origin is not None and "*" in self._allowed_origins:
            return "*"

        return None

    @staticmethod
    def build_allow_methods(methods: set[str]) -> str:
        """Build sorted comma delimited methods for Access-Control-Allow-Methods header

        Parameters
        ----------
        methods : set[str]
            Set of HTTP Methods

        Returns
        -------
        set[str]
            Formatted string with all HTTP Methods allowed for CORS e.g., `GET, OPTIONS`

        """
        return ",".join(sorted(methods))


class Response(Generic[ResponseT]):
    """Response data class that provides greater control over what is returned from the proxy event"""

    def __init__(
        self,
        status_code: int,
        content_type: str | None = None,
        body: ResponseT | None = None,
        headers: Mapping[str, str | list[str]] | None = None,
        cookies: list[Cookie] | None = None,
        compress: bool | None = None,
    ):
        """

        Parameters
        ----------
        status_code: int
            Http status code, example 200
        content_type: str
            Optionally set the Content-Type header, example "application/json". Note this will be merged into any
            provided http headers
        body: str | bytes | None
            Optionally set the response body. Note: bytes body will be automatically base64 encoded
        headers: Mapping[str, str | list[str]]
            Optionally set specific http headers. Setting "Content-Type" here would override the `content_type` value.
        cookies: list[Cookie]
            Optionally set cookies.
        """
        self.status_code = status_code
        self.body = body
        self.base64_encoded = False
        self.headers: dict[str, str | list[str]] = dict(headers) if headers else {}
        self.cookies = cookies or []
        self.compress = compress
        self.content_type = content_type
        if content_type:
            self.headers.setdefault("Content-Type", content_type)

    def is_json(self) -> bool:
        """
        Returns True if the response is JSON, based on the Content-Type.
        """
        content_type = self.headers.get("Content-Type", "")
        if isinstance(content_type, list):
            content_type = content_type[0]
        return content_type.startswith("application/json")


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
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str | None = None,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        middlewares: list[Callable[..., Response]] | None = None,
    ):
        """
        Internally used Route Configuration

        Parameters
        ----------
        method: str
            The HTTP method, example "GET"
        path: str
            The path of the route
        rule: Pattern
            The route rule, example "/my/path"
        func: Callable
            The route handler function
        cors: bool
            Whether or not to enable CORS for this route
        compress: bool
            Whether or not to enable gzip compression for this route
        cache_control: str | None
            The cache control header value, example "max-age=3600"
        summary: str | None
            The OpenAPI summary for this route
        description: str | None
            The OpenAPI description for this route
        responses: dict[int, OpenAPIResponse] | None
            The OpenAPI responses for this route
        response_description: str | None
            The OpenAPI response description for this route
        tags: list[str] | None
            The list of OpenAPI tags to be used for this route
        operation_id: str | None
            The OpenAPI operationId for this route
        include_in_schema: bool
            Whether or not to include this route in the OpenAPI schema
        security: list[dict[str, list[str]]], optional
            The OpenAPI security for this route
        openapi_extensions: dict[str, Any], optional
            Additional OpenAPI extensions as a dictionary.
        deprecated: bool
            Whether or not to mark this route as deprecated in the OpenAPI schema
        middlewares: list[Callable[..., Response]] | None
            The list of route middlewares to be called in order.
        """
        self.method = method.upper()
        self.path = "/" if path.strip() == "" else path

        # OpenAPI spec only understands paths with { }. So we'll have to convert Powertools' < >.
        # https://swagger.io/specification/#path-templating
        self.openapi_path = re.sub(r"<(.*?)>", lambda m: f"{{{''.join(m.group(1))}}}", self.path)

        self.rule = rule
        self.func = func
        self._middleware_stack = func
        self.cors = cors
        self.compress = compress
        self.cache_control = cache_control
        self.summary = summary
        self.description = description
        self.responses = responses
        self.response_description = response_description
        self.tags = tags or []
        self.include_in_schema = include_in_schema
        self.security = security
        self.openapi_extensions = openapi_extensions
        self.middlewares = middlewares or []
        self.operation_id = operation_id or self._generate_operation_id()
        self.deprecated = deprecated

        # _middleware_stack_built is used to ensure the middleware stack is only built once.
        self._middleware_stack_built = False

        # _dependant is used to cache the dependant model for the handler function
        self._dependant: Dependant | None = None

        # _body_field is used to cache the dependant model for the body field
        self._body_field: ModelField | None = None

    def __call__(
        self,
        router_middlewares: list[Callable],
        app: ApiGatewayResolver,
        route_arguments: dict[str, str],
    ) -> dict | tuple | Response:
        """Calling the Router class instance will trigger the following actions:
            1. If Route Middleware stack has not been built, build it
            2. Call the Route Middleware stack wrapping the original function
                handler with the app and route arguments.

        Parameters
        ----------
        router_middlewares: list[Callable]
            The list of Router Middlewares (assigned to ALL routes)
        app: "ApiGatewayResolver"
            The ApiGatewayResolver instance to pass into the middleware stack
        route_arguments: dict[str, str]
            The route arguments to pass to the app function (extracted from the Api Gateway
            Lambda Message structure from AWS)

        Returns
        -------
        dict | tuple | Response
            API Response object in ALL cases, except when the original API route
            handler is called which may also return a dict, tuple, or Response.
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

    def _build_middleware_stack(self, router_middlewares: list[Callable[..., Any]]) -> None:
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
        #   2. Adapt the response type of the route handler (dict | tuple | Response)
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

    @property
    def dependant(self) -> Dependant:
        if self._dependant is None:
            from aws_lambda_powertools.event_handler.openapi.dependant import get_dependant

            self._dependant = get_dependant(path=self.openapi_path, call=self.func, responses=self.responses)

        return self._dependant

    @property
    def body_field(self) -> ModelField | None:
        if self._body_field is None:
            from aws_lambda_powertools.event_handler.openapi.dependant import get_body_field

            self._body_field = get_body_field(dependant=self.dependant, name=self.operation_id)

        return self._body_field

    def _get_openapi_path(
        self,
        *,
        dependant: Dependant,
        operation_ids: set[str],
        model_name_map: dict[TypeModelOrEnum, str],
        field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Returns the OpenAPI path and definitions for the route.
        """
        from aws_lambda_powertools.event_handler.openapi.dependant import get_flat_params

        path = {}
        definitions: dict[str, Any] = {}

        # Gather all the route parameters
        operation = self._openapi_operation_metadata(operation_ids=operation_ids)
        parameters: list[dict[str, Any]] = []
        all_route_params = get_flat_params(dependant)
        operation_params = self._openapi_operation_parameters(
            all_route_params=all_route_params,
            model_name_map=model_name_map,
            field_mapping=field_mapping,
        )
        parameters.extend(operation_params)

        # Add security if present
        if self.security:
            operation["security"] = self.security

        # Add OpenAPI extensions if present
        if self.openapi_extensions:
            operation.update(self.openapi_extensions)

        # Add the parameters to the OpenAPI operation
        if parameters:
            all_parameters = {(param["in"], param["name"]): param for param in parameters}
            required_parameters = {(param["in"], param["name"]): param for param in parameters if param.get("required")}
            all_parameters.update(required_parameters)
            operation["parameters"] = list(all_parameters.values())

        # Add the request body to the OpenAPI operation, if applicable
        if self.method.upper() in METHODS_WITH_BODY:
            request_body_oai = self._openapi_operation_request_body(
                body_field=self.body_field,
                model_name_map=model_name_map,
                field_mapping=field_mapping,
            )
            if request_body_oai:
                operation["requestBody"] = request_body_oai

        # Validation failure response (422) will always be part of the schema
        operation_responses: dict[int, OpenAPIResponse] = {
            422: {
                "description": "Validation Error",
                "content": {"application/json": {"schema": {"$ref": f"{COMPONENT_REF_PREFIX}HTTPValidationError"}}},
            },
        }

        # Add the response to the OpenAPI operation
        if self.responses:
            for status_code in list(self.responses):
                response = self.responses[status_code]

                # Case 1: there is not 'content' key
                if "content" not in response:
                    response["content"] = {
                        "application/json": self._openapi_operation_return(
                            param=dependant.return_param,
                            model_name_map=model_name_map,
                            field_mapping=field_mapping,
                        ),
                    }

                # Case 2: there is a 'content' key
                else:
                    # Need to iterate to transform any 'model' into a 'schema'
                    for content_type, payload in response["content"].items():
                        new_payload: OpenAPIResponseContentSchema

                        # Case 2.1: the 'content' has a model
                        if "model" in payload:
                            # Find the model in the dependant's extra models
                            return_field = next(
                                filter(
                                    lambda model: model.type_ is cast(OpenAPIResponseContentModel, payload)["model"],
                                    self.dependant.response_extra_models,
                                ),
                            )
                            if not return_field:
                                raise AssertionError("Model declared in custom responses was not found")

                            new_payload = self._openapi_operation_return(
                                param=return_field,
                                model_name_map=model_name_map,
                                field_mapping=field_mapping,
                            )

                        # Case 2.2: the 'content' has a schema
                        else:
                            # Do nothing! We already have what we need!
                            new_payload = payload

                        response["content"][content_type] = new_payload

                # Merge the user provided response with the default responses
                operation_responses[status_code] = response
        else:
            # Set the default 200 response
            response_schema = self._openapi_operation_return(
                param=dependant.return_param,
                model_name_map=model_name_map,
                field_mapping=field_mapping,
            )

            # Add the response schema to the OpenAPI 200 response
            operation_responses[200] = {
                "description": self.response_description or _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
                "content": {"application/json": response_schema},
            }

        operation["responses"] = operation_responses
        path[self.method.lower()] = operation

        # Add the validation error schema to the definitions, but only if it hasn't been added yet
        if "ValidationError" not in definitions:
            definitions.update(
                {
                    "ValidationError": validation_error_definition,
                    "HTTPValidationError": validation_error_response_definition,
                },
            )

        # Generate the response schema
        return path, definitions

    def _openapi_operation_summary(self) -> str:
        """
        Returns the OpenAPI operation summary. If the user has not provided a summary, we
        generate one based on the route path and method.
        """
        return self.summary or f"{self.method.upper()} {self.openapi_path}"

    def _openapi_operation_metadata(self, operation_ids: set[str]) -> dict[str, Any]:
        """
        Returns the OpenAPI operation metadata. If the user has not provided a description, we
        generate one based on the route path and method.
        """
        operation: dict[str, Any] = {}

        # Ensure tags is added to the operation
        if self.tags:
            operation["tags"] = self.tags

        # Ensure summary is added to the operation
        operation["summary"] = self._openapi_operation_summary()

        # Ensure description is added to the operation
        if self.description:
            operation["description"] = self.description

        # Ensure operationId is unique
        if self.operation_id in operation_ids:
            message = f"Duplicate Operation ID {self.operation_id} for function {self.func.__name__}"
            file_name = getattr(self.func, "__globals__", {}).get("__file__")
            if file_name:
                message += f" in {file_name}"
            warnings.warn(message, stacklevel=1)

        # Adds the operation
        operation_ids.add(self.operation_id)
        operation["operationId"] = self.operation_id

        # Mark as deprecated if necessary
        operation["deprecated"] = self.deprecated or None

        return operation

    @staticmethod
    def _openapi_operation_request_body(
        *,
        body_field: ModelField | None,
        model_name_map: dict[TypeModelOrEnum, str],
        field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
    ) -> dict[str, Any] | None:
        """
        Returns the OpenAPI operation request body.
        """
        from aws_lambda_powertools.event_handler.openapi.compat import ModelField, get_schema_from_model_field
        from aws_lambda_powertools.event_handler.openapi.params import Body

        # Check that there is a body field and it's a Pydantic's model field
        if not body_field:
            return None

        if not isinstance(body_field, ModelField):
            raise AssertionError(f"Expected ModelField, got {body_field}")

        # Generate the request body schema
        body_schema = get_schema_from_model_field(
            field=body_field,
            model_name_map=model_name_map,
            field_mapping=field_mapping,
        )

        field_info = cast(Body, body_field.field_info)
        request_media_type = field_info.media_type
        required = body_field.required
        request_body_oai: dict[str, Any] = {}
        if required:
            request_body_oai["required"] = required

        if field_info.description:
            request_body_oai["description"] = field_info.description

        # Generate the request body media type
        request_media_content: dict[str, Any] = {"schema": body_schema}
        request_body_oai["content"] = {request_media_type: request_media_content}
        return request_body_oai

    @staticmethod
    def _openapi_operation_parameters(
        *,
        all_route_params: Sequence[ModelField],
        model_name_map: dict[TypeModelOrEnum, str],
        field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
    ) -> list[dict[str, Any]]:
        """
        Returns the OpenAPI operation parameters.
        """
        from aws_lambda_powertools.event_handler.openapi.compat import (
            get_schema_from_model_field,
        )
        from aws_lambda_powertools.event_handler.openapi.params import Param

        parameters = []
        parameter: dict[str, Any] = {}

        for param in all_route_params:
            field_info = param.field_info
            field_info = cast(Param, field_info)
            if not field_info.include_in_schema:
                continue

            param_schema = get_schema_from_model_field(
                field=param,
                model_name_map=model_name_map,
                field_mapping=field_mapping,
            )

            parameter = {
                "name": param.alias,
                "in": field_info.in_.value,
                "required": param.required,
                "schema": param_schema,
            }

            if field_info.description:
                parameter["description"] = field_info.description

            if field_info.openapi_examples:
                parameter["examples"] = field_info.openapi_examples

            if field_info.deprecated:
                parameter["deprecated"] = field_info.deprecated

            parameters.append(parameter)

        return parameters

    @staticmethod
    def _openapi_operation_return(
        *,
        param: ModelField | None,
        model_name_map: dict[TypeModelOrEnum, str],
        field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
    ) -> OpenAPIResponseContentSchema:
        """
        Returns the OpenAPI operation return.
        """
        if param is None:
            return {}

        from aws_lambda_powertools.event_handler.openapi.compat import (
            get_schema_from_model_field,
        )

        return_schema = get_schema_from_model_field(
            field=param,
            model_name_map=model_name_map,
            field_mapping=field_mapping,
        )

        return {"schema": return_schema}

    def _generate_operation_id(self) -> str:
        operation_id = self.func.__name__ + self.openapi_path
        operation_id = re.sub(r"\W", "_", operation_id)
        operation_id = operation_id + "_" + self.method.lower()
        return operation_id


class ResponseBuilder(Generic[ResponseEventT]):
    """Internally used Response builder"""

    def __init__(
        self,
        response: Response,
        serializer: Callable[[Any], str] = partial(json.dumps, separators=(",", ":"), cls=Encoder),
        route: Route | None = None,
    ):
        self.response = response
        self.serializer = serializer
        self.route = route

    def _add_cors(self, event: ResponseEventT, cors: CORSConfig):
        """Update headers to include the configured Access-Control headers"""
        extracted_origin_header = extract_origin_header(event.resolved_headers_field)

        origin = cors.allowed_origin(extracted_origin_header)
        if origin is not None:
            self.response.headers.update(cors.to_dict(origin))

    def _add_cache_control(self, cache_control: str):
        """Set the specified cache control headers for 200 http responses. For non-200 `no-cache` is used."""
        cache_control = cache_control if self.response.status_code == 200 else "no-cache"
        self.response.headers["Cache-Control"] = cache_control

    @staticmethod
    def _has_compression_enabled(
        route_compression: bool,
        response_compression: bool | None,
        event: ResponseEventT,
    ) -> bool:
        """
        Checks if compression is enabled.

        NOTE: Response compression takes precedence.

        Parameters
        ----------
        route_compression: bool, optional
            A boolean indicating whether compression is enabled or not in the route setting.
        response_compression: bool, optional
            A boolean indicating whether compression is enabled or not in the response setting.
        event: ResponseEventT
            The event object containing the request details.

        Returns
        -------
        bool
            True if compression is enabled and the "gzip" encoding is accepted, False otherwise.
        """
        encoding = event.headers.get("accept-encoding", "")
        if "gzip" in encoding:
            if response_compression is not None:
                return response_compression  # e.g., Response(compress=False/True))
            if route_compression:
                return True  # e.g., @app.get(compress=True)

        return False

    def _compress(self):
        """Compress the response body, but only if `Accept-Encoding` headers includes gzip."""
        self.response.headers["Content-Encoding"] = "gzip"
        if isinstance(self.response.body, str):
            logger.debug("Converting string response to bytes before compressing it")
            self.response.body = bytes(self.response.body, "utf-8")
        gzip = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
        self.response.body = gzip.compress(self.response.body) + gzip.flush()

    def _route(self, event: ResponseEventT, cors: CORSConfig | None):
        """Optionally handle any of the route's configure response handling"""
        if self.route is None:
            return
        if self.route.cors:
            self._add_cors(event, cors or CORSConfig())
        if self.route.cache_control:
            self._add_cache_control(self.route.cache_control)
        if self._has_compression_enabled(
            route_compression=self.route.compress,
            response_compression=self.response.compress,
            event=event,
        ):
            self._compress()

    def build(self, event: ResponseEventT, cors: CORSConfig | None = None) -> dict[str, Any]:
        """Build the full response dict to be returned by the lambda"""

        # We only apply the serializer when the content type is JSON and the
        # body is not a str, to avoid double encoding
        if self.response.is_json() and not isinstance(self.response.body, str):
            self.response.body = self.serializer(self.response.body)

        self._route(event, cors)

        if isinstance(self.response.body, bytes):
            logger.debug("Encoding bytes response with base64")
            self.response.base64_encoded = True
            self.response.body = base64.b64encode(self.response.body).decode()

        return {
            "statusCode": self.response.status_code,
            "body": self.response.body,
            "isBase64Encoded": self.response.base64_encoded,
            **event.header_serializer().serialize(headers=self.response.headers, cookies=self.response.cookies),
        }


class BaseRouter(ABC):
    """Base class for Routing"""

    current_event: BaseProxyEvent
    lambda_context: LambdaContext
    context: dict
    _router_middlewares: list[Callable] = []
    processed_stack_frames: list[str] = []

    @abstractmethod
    def route(
        self,
        rule: str,
        method: Any,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> Callable[[AnyCallableT], AnyCallableT]:
        raise NotImplementedError()

    def use(self, middlewares: list[Callable[..., Response]]) -> None:
        """
        Add one or more global middlewares that run before/after route specific middleware.

        NOTE: Middlewares are called in insertion order.

        Parameters
        ----------
        middlewares: list[Callable[..., Response]]
            List of global middlewares to be used

        Examples
        --------

        Add middlewares to be used for every request processed by the Router.

        ```python
        from aws_lambda_powertools import Logger
        from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
        from aws_lambda_powertools.event_handler.middlewares import NextMiddleware

        logger = Logger()
        app = APIGatewayRestResolver()

        def log_request_response(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
            logger.info("Incoming request", path=app.current_event.path, request=app.current_event.raw_event)

            result = next_middleware(app)
            logger.info("Response received", response=result.__dict__)

            return result

        app.use(middlewares=[log_request_response])


        def lambda_handler(event, context):
            return app.resolve(event, context)
        ```
        """
        self._router_middlewares = self._router_middlewares + middlewares

    def get(
        self,
        rule: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> Callable[[AnyCallableT], AnyCallableT]:
        """Get route decorator with GET `method`

        Examples
        --------
        Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

        ```python
        from aws_lambda_powertools import Tracer
        from aws_lambda_powertools.event_handler import APIGatewayRestResolver

        tracer = Tracer()
        app = APIGatewayRestResolver()

        @app.get("/get-call")
        def simple_get():
            return {"message": "Foo"}

        @tracer.capture_lambda_handler
        def lambda_handler(event, context):
            return app.resolve(event, context)
        ```
        """
        return self.route(
            rule,
            "GET",
            cors,
            compress,
            cache_control,
            summary,
            description,
            responses,
            response_description,
            tags,
            operation_id,
            include_in_schema,
            security,
            openapi_extensions,
            deprecated,
            middlewares,
        )

    def post(
        self,
        rule: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> Callable[[AnyCallableT], AnyCallableT]:
        """Post route decorator with POST `method`

        Examples
        --------
        Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

        ```python
        from aws_lambda_powertools import Tracer
        from aws_lambda_powertools.event_handler import APIGatewayRestResolver

        tracer = Tracer()
        app = APIGatewayRestResolver()

        @app.post("/post-call")
        def simple_post():
            post_data: dict = app.current_event.json_body
            return {"message": post_data["value"]}

        @tracer.capture_lambda_handler
        def lambda_handler(event, context):
            return app.resolve(event, context)
        ```
        """
        return self.route(
            rule,
            "POST",
            cors,
            compress,
            cache_control,
            summary,
            description,
            responses,
            response_description,
            tags,
            operation_id,
            include_in_schema,
            security,
            openapi_extensions,
            deprecated,
            middlewares,
        )

    def put(
        self,
        rule: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> Callable[[AnyCallableT], AnyCallableT]:
        """Put route decorator with PUT `method`

        Examples
        --------
        Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

        ```python
        from aws_lambda_powertools import Tracer
        from aws_lambda_powertools.event_handler import APIGatewayRestResolver

        tracer = Tracer()
        app = APIGatewayRestResolver()

        @app.put("/put-call")
        def simple_put():
            put_data: dict = app.current_event.json_body
            return {"message": put_data["value"]}

        @tracer.capture_lambda_handler
        def lambda_handler(event, context):
            return app.resolve(event, context)
        ```
        """
        return self.route(
            rule,
            "PUT",
            cors,
            compress,
            cache_control,
            summary,
            description,
            responses,
            response_description,
            tags,
            operation_id,
            include_in_schema,
            security,
            openapi_extensions,
            deprecated,
            middlewares,
        )

    def delete(
        self,
        rule: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> Callable[[AnyCallableT], AnyCallableT]:
        """Delete route decorator with DELETE `method`

        Examples
        --------
        Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

        ```python
        from aws_lambda_powertools import Tracer
        from aws_lambda_powertools.event_handler import APIGatewayRestResolver

        tracer = Tracer()
        app = APIGatewayRestResolver()

        @app.delete("/delete-call")
        def simple_delete():
            return {"message": "deleted"}

        @tracer.capture_lambda_handler
        def lambda_handler(event, context):
            return app.resolve(event, context)
        ```
        """
        return self.route(
            rule,
            "DELETE",
            cors,
            compress,
            cache_control,
            summary,
            description,
            responses,
            response_description,
            tags,
            operation_id,
            include_in_schema,
            security,
            openapi_extensions,
            deprecated,
            middlewares,
        )

    def patch(
        self,
        rule: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        middlewares: list[Callable] | None = None,
    ) -> Callable[[AnyCallableT], AnyCallableT]:
        """Patch route decorator with PATCH `method`

        Examples
        --------
        Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

        ```python
        from aws_lambda_powertools import Tracer
        from aws_lambda_powertools.event_handler import APIGatewayRestResolver

        tracer = Tracer()
        app = APIGatewayRestResolver()

        @app.patch("/patch-call")
        def simple_patch():
            patch_data: dict = app.current_event.json_body
            patch_data["value"] = patched

            return {"message": patch_data}

        @tracer.capture_lambda_handler
        def lambda_handler(event, context):
            return app.resolve(event, context)
        ```
        """
        return self.route(
            rule,
            "PATCH",
            cors,
            compress,
            cache_control,
            summary,
            description,
            responses,
            response_description,
            tags,
            operation_id,
            include_in_schema,
            security,
            openapi_extensions,
            deprecated,
            middlewares,
        )

    def head(
        self,
        rule: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        middlewares: list[Callable] | None = None,
    ) -> Callable[[AnyCallableT], AnyCallableT]:
        """Head route decorator with HEAD `method`

        Examples
        --------
        Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

        ```python
        from aws_lambda_powertools import Tracer
        from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response, content_types

        tracer = Tracer()
        app = APIGatewayRestResolver()

        @app.head("/head-call")
        def simple_head():
            return Response(status_code=200,
                            content_type=content_types.APPLICATION_JSON,
                            headers={"Content-Length": "123"})

        @tracer.capture_lambda_handler
        def lambda_handler(event, context):
            return app.resolve(event, context)
        ```
        """
        return self.route(
            rule,
            "HEAD",
            cors,
            compress,
            cache_control,
            summary,
            description,
            responses,
            response_description,
            tags,
            operation_id,
            include_in_schema,
            security,
            openapi_extensions,
            deprecated,
            middlewares,
        )

    def _push_processed_stack_frame(self, frame: str):
        """
        Add Current Middleware to the Middleware Stack Frames
        The stack frames will be used when exceptions are thrown and Powertools
        debug is enabled by developers.
        """
        self.processed_stack_frames.append(frame)

    def _reset_processed_stack(self):
        """Reset the Processed Stack Frames"""
        self.processed_stack_frames.clear()

    def append_context(self, **additional_context):
        """Append key=value data as routing context"""
        self.context.update(**additional_context)

    def clear_context(self):
        """Resets routing context"""
        self.context.clear()


class MiddlewareFrame:
    """
    Creates a Middle Stack Wrapper instance to be used as a "Frame" in the overall stack of
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

    def __call__(self, app: ApiGatewayResolver) -> dict | tuple | Response:
        """
        Call the middleware Frame to process the request.

        Parameters
        ----------
        app: BaseRouter
            The router instance

        Returns
        -------
        dict | tuple | Response
            (tech-debt for backward compatibility).  The response type should be a
            Response object in all cases excepting when the original API route handler
            is called which will return one of 3 outputs.

        """
        # Do debug printing and push processed stack frame AFTER calling middleware
        # else the stack frame text of `current calling next` is confusing.
        logger.debug("MiddlewareFrame: %s", self)
        app._push_processed_stack_frame(str(self))

        return self.current_middleware(app, self.next_middleware)


def _registered_api_adapter(app: ApiGatewayResolver, next_middleware: Callable[..., Any]) -> dict | tuple | Response:
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
    route_args: dict = app.context.get("_route_args", {})
    logger.debug(f"Calling API Route Handler: {route_args}")
    return app._to_response(next_middleware(**route_args))


class ApiGatewayResolver(BaseRouter):
    """API Gateway, VPC Laticce, Bedrock and ALB proxy resolver

    Examples
    --------
    Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

    ```python
    from aws_lambda_powertools import Tracer
    from aws_lambda_powertools.event_handler import APIGatewayRestResolver

    tracer = Tracer()
    app = APIGatewayRestResolver()

    @app.get("/get-call")
    def simple_get():
        return {"message": "Foo"}

    @app.post("/post-call")
    def simple_post():
        post_data: dict = app.current_event.json_body
        return {"message": post_data["value"]}

    @tracer.capture_lambda_handler
    def lambda_handler(event, context):
        return app.resolve(event, context)
    ```
    """

    def __init__(
        self,
        proxy_type: Enum = ProxyEventType.APIGatewayProxyEvent,
        cors: CORSConfig | None = None,
        debug: bool | None = None,
        serializer: Callable[[dict], str] | None = None,
        strip_prefixes: list[str | Pattern] | None = None,
        enable_validation: bool = False,
        response_validation_error_http_code: HTTPStatus | int | None = None,
    ):
        """
        Parameters
        ----------
        proxy_type: ProxyEventType
            Proxy request type, defaults to API Gateway V1
        cors: CORSConfig
            Optionally configure and enabled CORS. Not each route will need to have to cors=True
        debug: bool | None
            Enables debug mode, by default False. Can be also be enabled by "POWERTOOLS_DEV"
            environment variable
        serializer: Callable, optional
            function to serialize `obj` to a JSON formatted `str`, by default json.dumps
        strip_prefixes: list[str | Pattern], optional
            optional list of prefixes to be removed from the request path before doing the routing.
            This is often used with api gateways with multiple custom mappings.
            Each prefix can be a static string or a compiled regex pattern
        enable_validation: bool | None
            Enables validation of the request body against the route schema, by default False.
        response_validation_error_http_code
            Sets the returned status code if response is not validated. enable_validation must be True.
        """
        self._proxy_type = proxy_type
        self._dynamic_routes: list[Route] = []
        self._static_routes: list[Route] = []
        self._route_keys: list[str] = []
        self._exception_handlers: dict[type, Callable] = {}
        self._cors = cors
        self._cors_enabled: bool = cors is not None
        self._cors_methods: set[str] = {"OPTIONS"}
        self._debug = self._has_debug(debug)
        self._enable_validation = enable_validation
        self._strip_prefixes = strip_prefixes
        self.context: dict = {}  # early init as customers might add context before event resolution
        self.processed_stack_frames = []
        self._response_builder_class = ResponseBuilder[BaseProxyEvent]
        self.openapi_config = OpenAPIConfig()  # starting an empty dataclass
        self._has_response_validation_error = response_validation_error_http_code is not None
        self._response_validation_error_http_code = self._validate_response_validation_error_http_code(
            response_validation_error_http_code,
            enable_validation,
        )

        # Allow for a custom serializer or a concise json serialization
        self._serializer = serializer or partial(json.dumps, separators=(",", ":"), cls=Encoder)

        if self._enable_validation:
            from aws_lambda_powertools.event_handler.middlewares.openapi_validation import OpenAPIValidationMiddleware

            # Note the serializer argument: only use custom serializer if provided by the caller
            # Otherwise, fully rely on the internal Pydantic based mechanism to serialize responses for validation.
            self.use(
                [
                    OpenAPIValidationMiddleware(
                        validation_serializer=serializer,
                        has_response_validation_error=self._has_response_validation_error,
                    ),
                ],
            )

    def _validate_response_validation_error_http_code(
        self,
        response_validation_error_http_code: HTTPStatus | int | None,
        enable_validation: bool,
    ) -> HTTPStatus:
        if response_validation_error_http_code and not enable_validation:
            msg = "'response_validation_error_http_code' cannot be set when enable_validation is False."
            raise ValueError(msg)

        if (
            not isinstance(response_validation_error_http_code, HTTPStatus)
            and response_validation_error_http_code is not None
        ):

            try:
                response_validation_error_http_code = HTTPStatus(response_validation_error_http_code)
            except ValueError:
                msg = f"'{response_validation_error_http_code}' must be an integer representing an HTTP status code."
                raise ValueError(msg) from None

        return response_validation_error_http_code or HTTPStatus.UNPROCESSABLE_ENTITY

    def get_openapi_schema(
        self,
        *,
        title: str = DEFAULT_OPENAPI_TITLE,
        version: str = DEFAULT_API_VERSION,
        openapi_version: str = DEFAULT_OPENAPI_VERSION,
        summary: str | None = None,
        description: str | None = None,
        tags: list[Tag | str] | None = None,
        servers: list[Server] | None = None,
        terms_of_service: str | None = None,
        contact: Contact | None = None,
        license_info: License | None = None,
        security_schemes: dict[str, SecurityScheme] | None = None,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
    ) -> OpenAPI:
        """
        Returns the OpenAPI schema as a pydantic model.

        Parameters
        ----------
        title: str
            The title of the application.
        version: str
            The version of the OpenAPI document (which is distinct from the OpenAPI Specification version or the API
        openapi_version: str, default = "3.0.0"
            The version of the OpenAPI Specification (which the document uses).
        summary: str, optional
            A short summary of what the application does.
        description: str, optional
            A verbose explanation of the application behavior.
        tags: list[Tag | str], optional
            A list of tags used by the specification with additional metadata.
        servers: list[Server], optional
            An array of Server Objects, which provide connectivity information to a target server.
        terms_of_service: str, optional
            A URL to the Terms of Service for the API. MUST be in the format of a URL.
        contact: Contact, optional
            The contact information for the exposed API.
        license_info: License, optional
            The license information for the exposed API.
        security_schemes: dict[str, SecurityScheme]], optional
            A declaration of the security schemes available to be used in the specification.
        security: list[dict[str, list[str]]], optional
            A declaration of which security mechanisms are applied globally across the API.
        openapi_extensions: Dict[str, Any], optional
            Additional OpenAPI extensions as a dictionary.

        Returns
        -------
        OpenAPI: pydantic model
            The OpenAPI schema as a pydantic model.
        """

        # DEPRECATION: Will be removed in v4.0.0. Use configure_api() instead.
        # Maintained for backwards compatibility.
        # See: https://github.com/aws-powertools/powertools-lambda-python/issues/6122
        if title == DEFAULT_OPENAPI_TITLE and self.openapi_config.title:
            title = self.openapi_config.title

        if version == DEFAULT_API_VERSION and self.openapi_config.version:
            version = self.openapi_config.version

        if openapi_version == DEFAULT_OPENAPI_VERSION and self.openapi_config.openapi_version:
            openapi_version = self.openapi_config.openapi_version

        summary = summary or self.openapi_config.summary
        description = description or self.openapi_config.description
        tags = tags or self.openapi_config.tags
        servers = servers or self.openapi_config.servers
        terms_of_service = terms_of_service or self.openapi_config.terms_of_service
        contact = contact or self.openapi_config.contact
        license_info = license_info or self.openapi_config.license_info
        security_schemes = security_schemes or self.openapi_config.security_schemes
        security = security or self.openapi_config.security
        openapi_extensions = openapi_extensions or self.openapi_config.openapi_extensions

        from aws_lambda_powertools.event_handler.openapi.compat import (
            GenerateJsonSchema,
            get_compat_model_name_map,
            get_definitions,
        )
        from aws_lambda_powertools.event_handler.openapi.models import OpenAPI, PathItem, Tag
        from aws_lambda_powertools.event_handler.openapi.types import (
            COMPONENT_REF_TEMPLATE,
        )

        openapi_version = self._determine_openapi_version(openapi_version)

        # Start with the bare minimum required for a valid OpenAPI schema
        info: dict[str, Any] = {"title": title, "version": version}

        optional_fields = {
            "summary": summary,
            "description": description,
            "termsOfService": terms_of_service,
            "contact": contact,
            "license": license_info,
        }

        info.update({field: value for field, value in optional_fields.items() if value})

        if not isinstance(openapi_extensions, dict):
            openapi_extensions = {}

        output: dict[str, Any] = {
            "openapi": openapi_version,
            "info": info,
            "servers": self._get_openapi_servers(servers),
            "security": self._get_openapi_security(security, security_schemes),
            **openapi_extensions,
        }

        components: dict[str, dict[str, Any]] = {}
        paths: dict[str, dict[str, Any]] = {}
        operation_ids: set[str] = set()

        all_routes = self._dynamic_routes + self._static_routes
        all_fields = self._get_fields_from_routes(all_routes)
        model_name_map = get_compat_model_name_map(all_fields)

        # Collect all models and definitions
        schema_generator = GenerateJsonSchema(ref_template=COMPONENT_REF_TEMPLATE)
        field_mapping, definitions = get_definitions(
            fields=all_fields,
            schema_generator=schema_generator,
            model_name_map=model_name_map,
        )

        # Add routes to the OpenAPI schema
        for route in all_routes:
            if route.security and not _validate_openapi_security_parameters(
                security=route.security,
                security_schemes=security_schemes,
            ):
                raise SchemaValidationError(
                    "Security configuration was not found in security_schemas or security_schema was not defined. "
                    "See: https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/api_gateway/#security-schemes",
                )

            if not route.include_in_schema:
                continue

            result = route._get_openapi_path(
                dependant=route.dependant,
                operation_ids=operation_ids,
                model_name_map=model_name_map,
                field_mapping=field_mapping,
            )
            if result:
                path, path_definitions = result
                if path:
                    paths.setdefault(route.openapi_path, {}).update(path)
                if path_definitions:
                    definitions.update(path_definitions)

        if definitions:
            components["schemas"] = {k: definitions[k] for k in sorted(definitions)}
        if security_schemes:
            components["securitySchemes"] = security_schemes
        if components:
            output["components"] = components
        if tags:
            output["tags"] = [Tag(name=tag) if isinstance(tag, str) else tag for tag in tags]

        output["paths"] = {k: PathItem(**v) for k, v in paths.items()}

        return OpenAPI(**output)

    @staticmethod
    def _get_openapi_servers(servers: list[Server] | None) -> list[Server]:
        from aws_lambda_powertools.event_handler.openapi.models import Server

        # If the 'servers' property is not provided or is an empty array,
        # the default behavior is to return a Server Object with a URL value of "/".
        return servers or [Server(url="/")]

    @staticmethod
    def _get_openapi_security(
        security: list[dict[str, list[str]]] | None,
        security_schemes: dict[str, SecurityScheme] | None,
    ) -> list[dict[str, list[str]]] | None:
        if not security:
            return None

        if not _validate_openapi_security_parameters(security=security, security_schemes=security_schemes):
            raise SchemaValidationError(
                "Security configuration was not found in security_schemas or security_schema was not defined. "
                "See: https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/api_gateway/#security-schemes",
            )

        return security

    @staticmethod
    def _determine_openapi_version(openapi_version: str):
        # Pydantic V2 has no support for OpenAPI schema 3.0
        if not openapi_version.startswith("3.1"):
            warnings.warn(
                "You are using Pydantic v2, which is incompatible with OpenAPI schema 3.0. Forcing OpenAPI 3.1",
                stacklevel=2,
            )
            openapi_version = "3.1.0"
        return openapi_version

    def get_openapi_json_schema(
        self,
        *,
        title: str = DEFAULT_OPENAPI_TITLE,
        version: str = DEFAULT_API_VERSION,
        openapi_version: str = DEFAULT_OPENAPI_VERSION,
        summary: str | None = None,
        description: str | None = None,
        tags: list[Tag | str] | None = None,
        servers: list[Server] | None = None,
        terms_of_service: str | None = None,
        contact: Contact | None = None,
        license_info: License | None = None,
        security_schemes: dict[str, SecurityScheme] | None = None,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
    ) -> str:
        """
        Returns the OpenAPI schema as a JSON serializable dict

        Parameters
        ----------
        title: str
            The title of the application.
        version: str
            The version of the OpenAPI document (which is distinct from the OpenAPI Specification version or the API
        openapi_version: str, default = "3.0.0"
            The version of the OpenAPI Specification (which the document uses).
        summary: str, optional
            A short summary of what the application does.
        description: str, optional
            A verbose explanation of the application behavior.
        tags: list[Tag, str], optional
            A list of tags used by the specification with additional metadata.
        servers: list[Server], optional
            An array of Server Objects, which provide connectivity information to a target server.
        terms_of_service: str, optional
            A URL to the Terms of Service for the API. MUST be in the format of a URL.
        contact: Contact, optional
            The contact information for the exposed API.
        license_info: License, optional
            The license information for the exposed API.
        security_schemes: dict[str, SecurityScheme]], optional
            A declaration of the security schemes available to be used in the specification.
        security: list[dict[str, list[str]]], optional
            A declaration of which security mechanisms are applied globally across the API.
        openapi_extensions: Dict[str, Any], optional
            Additional OpenAPI extensions as a dictionary.

        Returns
        -------
        str
            The OpenAPI schema as a JSON serializable dict.
        """

        from aws_lambda_powertools.event_handler.openapi.compat import model_json

        return model_json(
            self.get_openapi_schema(
                title=title,
                version=version,
                openapi_version=openapi_version,
                summary=summary,
                description=description,
                tags=tags,
                servers=servers,
                terms_of_service=terms_of_service,
                contact=contact,
                license_info=license_info,
                security_schemes=security_schemes,
                security=security,
                openapi_extensions=openapi_extensions,
            ),
            by_alias=True,
            exclude_none=True,
            indent=2,
        )

    def configure_openapi(
        self,
        title: str = DEFAULT_OPENAPI_TITLE,
        version: str = DEFAULT_API_VERSION,
        openapi_version: str = DEFAULT_OPENAPI_VERSION,
        summary: str | None = None,
        description: str | None = None,
        tags: list[Tag | str] | None = None,
        servers: list[Server] | None = None,
        terms_of_service: str | None = None,
        contact: Contact | None = None,
        license_info: License | None = None,
        security_schemes: dict[str, SecurityScheme] | None = None,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
    ):
        """Configure OpenAPI specification settings for the API.

        Sets up the OpenAPI documentation configuration that can be later used
        when enabling Swagger UI or generating OpenAPI specifications.

        Parameters
        ----------
        title: str
            The title of the application.
        version: str
            The version of the OpenAPI document (which is distinct from the OpenAPI Specification version or the API
        openapi_version: str, default = "3.0.0"
            The version of the OpenAPI Specification (which the document uses).
        summary: str, optional
            A short summary of what the application does.
        description: str, optional
            A verbose explanation of the application behavior.
        tags: list[Tag, str], optional
            A list of tags used by the specification with additional metadata.
        servers: list[Server], optional
            An array of Server Objects, which provide connectivity information to a target server.
        terms_of_service: str, optional
            A URL to the Terms of Service for the API. MUST be in the format of a URL.
        contact: Contact, optional
            The contact information for the exposed API.
        license_info: License, optional
            The license information for the exposed API.
        security_schemes: dict[str, SecurityScheme]], optional
            A declaration of the security schemes available to be used in the specification.
        security: list[dict[str, list[str]]], optional
            A declaration of which security mechanisms are applied globally across the API.
        openapi_extensions: Dict[str, Any], optional
            Additional OpenAPI extensions as a dictionary.

        Example
        --------
        >>> api.configure_openapi(
        ...     title="My API",
        ...     version="1.0.0",
        ...     description="API for managing resources",
        ...     contact=Contact(
        ...         name="API Support",
        ...         email="support@example.com"
        ...     )
        ... )

        See Also
        --------
        enable_swagger : Method to enable Swagger UI using these configurations
        OpenAPIConfig : Data class containing all OpenAPI configuration options
        """
        self.openapi_config = OpenAPIConfig(
            title=title,
            version=version,
            openapi_version=openapi_version,
            summary=summary,
            description=description,
            tags=tags,
            servers=servers,
            terms_of_service=terms_of_service,
            contact=contact,
            license_info=license_info,
            security_schemes=security_schemes,
            security=security,
            openapi_extensions=openapi_extensions,
        )

    def enable_swagger(
        self,
        *,
        path: str = "/swagger",
        title: str = DEFAULT_OPENAPI_TITLE,
        version: str = DEFAULT_API_VERSION,
        openapi_version: str = DEFAULT_OPENAPI_VERSION,
        summary: str | None = None,
        description: str | None = None,
        tags: list[Tag | str] | None = None,
        servers: list[Server] | None = None,
        terms_of_service: str | None = None,
        contact: Contact | None = None,
        license_info: License | None = None,
        swagger_base_url: str | None = None,
        middlewares: list[Callable[..., Response]] | None = None,
        compress: bool = False,
        security_schemes: dict[str, SecurityScheme] | None = None,
        security: list[dict[str, list[str]]] | None = None,
        oauth2_config: OAuth2Config | None = None,
        persist_authorization: bool = False,
        openapi_extensions: dict[str, Any] | None = None,
    ):
        """
        Returns the OpenAPI schema as a JSON serializable dict

        Parameters
        ----------
        path: str, default = "/swagger"
            The path to the swagger UI.
        title: str
            The title of the application.
        version: str
            The version of the OpenAPI document (which is distinct from the OpenAPI Specification version or the API
        openapi_version: str, default = "3.0.0"
            The version of the OpenAPI Specification (which the document uses).
        summary: str, optional
            A short summary of what the application does.
        description: str, optional
            A verbose explanation of the application behavior.
        tags: list[Tag, str], optional
            A list of tags used by the specification with additional metadata.
        servers: list[Server], optional
            An array of Server Objects, which provide connectivity information to a target server.
        terms_of_service: str, optional
            A URL to the Terms of Service for the API. MUST be in the format of a URL.
        contact: Contact, optional
            The contact information for the exposed API.
        license_info: License, optional
            The license information for the exposed API.
        swagger_base_url: str, optional
            The base url for the swagger UI. If not provided, we will serve a recent version of the Swagger UI.
        middlewares: list[Callable[..., Response]], optional
            List of middlewares to be used for the swagger route.
        compress: bool, default = False
            Whether or not to enable gzip compression swagger route.
        security_schemes: dict[str, "SecurityScheme"], optional
            A declaration of the security schemes available to be used in the specification.
        security: list[dict[str, list[str]]], optional
            A declaration of which security mechanisms are applied globally across the API.
        oauth2_config: OAuth2Config, optional
            The OAuth2 configuration for the Swagger UI.
        persist_authorization: bool, optional
            Whether to persist authorization data on browser close/refresh.
        openapi_extensions: dict[str, Any], optional
            Additional OpenAPI extensions as a dictionary.
        """

        from aws_lambda_powertools.event_handler.openapi.compat import model_json
        from aws_lambda_powertools.event_handler.openapi.models import Server
        from aws_lambda_powertools.event_handler.openapi.swagger_ui import (
            generate_oauth2_redirect_html,
            generate_swagger_html,
        )

        @self.get(path, middlewares=middlewares, include_in_schema=False, compress=compress)
        def swagger_handler():
            query_params = self.current_event.query_string_parameters or {}

            # Check for query parameters; if "format" is specified as "oauth2-redirect",
            # send the oauth2-redirect HTML stanza so OAuth2 can be used
            # Source: https://github.com/swagger-api/swagger-ui/blob/master/dist/oauth2-redirect.html
            if query_params.get("format") == "oauth2-redirect":
                return Response(
                    status_code=200,
                    content_type="text/html",
                    body=generate_oauth2_redirect_html(),
                )

            base_path = self._get_base_path()

            if swagger_base_url:
                swagger_js = f"{swagger_base_url}/swagger-ui-bundle.min.js"
                swagger_css = f"{swagger_base_url}/swagger-ui.min.css"
            else:
                # We now inject CSS and JS into the SwaggerUI file
                swagger_js = Path.open(
                    Path(__file__).parent / "openapi" / "swagger_ui" / "swagger-ui-bundle.min.js",
                ).read()
                swagger_css = Path.open(Path(__file__).parent / "openapi" / "swagger_ui" / "swagger-ui.min.css").read()

            openapi_servers = servers or [Server(url=(base_path or "/"))]

            spec = self.get_openapi_schema(
                title=title,
                version=version,
                openapi_version=openapi_version,
                summary=summary,
                description=description,
                tags=tags,
                servers=openapi_servers,
                terms_of_service=terms_of_service,
                contact=contact,
                license_info=license_info,
                security_schemes=security_schemes,
                security=security,
                openapi_extensions=openapi_extensions,
            )

            # The .replace('</', '<\\/') part is necessary to prevent a potential issue where the JSON string contains
            # </script> or similar tags. Escaping the forward slash in </ as <\/ ensures that the JSON does not
            # inadvertently close the script tag, and the JSON remains a valid string within the JavaScript code.
            escaped_spec = model_json(
                spec,
                by_alias=True,
                exclude_none=True,
                indent=2,
            ).replace("</", "<\\/")

            # Check for query parameters; if "format" is specified as "json",
            # respond with the JSON used in the OpenAPI spec
            # Example: https://www.example.com/swagger?format=json
            if query_params.get("format") == "json":
                return Response(
                    status_code=200,
                    content_type="application/json",
                    body=escaped_spec,
                )

            body = generate_swagger_html(
                escaped_spec,
                swagger_js,
                swagger_css,
                swagger_base_url,
                oauth2_config,
                persist_authorization,
            )

            return Response(
                status_code=200,
                content_type="text/html",
                body=body,
            )

    def route(
        self,
        rule: str,
        method: str | list[str] | tuple[str],
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> Callable[[AnyCallableT], AnyCallableT]:
        """Route decorator includes parameter `method`"""

        def register_resolver(func: AnyCallableT) -> AnyCallableT:
            methods = (method,) if isinstance(method, str) else method
            logger.debug(f"Adding route using rule {rule} and methods: {','.join(m.upper() for m in methods)}")

            cors_enabled = self._cors_enabled if cors is None else cors

            for item in methods:
                _route = Route(
                    item,
                    rule,
                    self._compile_regex(rule),
                    func,
                    cors_enabled,
                    compress,
                    cache_control,
                    summary,
                    description,
                    responses,
                    response_description,
                    tags,
                    operation_id,
                    include_in_schema,
                    security,
                    openapi_extensions,
                    deprecated,
                    middlewares,
                )

                # The more specific route wins.
                # We store dynamic (/studies/{studyid}) and static routes (/studies/fetch) separately.
                # Then attempt a match for static routes before dynamic routes.
                # This ensures that the most specific route is prioritized and processed first (studies/fetch).
                if _route.rule.groups > 0:
                    self._dynamic_routes.append(_route)
                else:
                    self._static_routes.append(_route)

                self._create_route_key(item, rule)

                if cors_enabled:
                    logger.debug(f"Registering method {item.upper()} to Allow Methods in CORS")
                    self._cors_methods.add(item.upper())

            return func

        return register_resolver

    def resolve(self, event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
        """Resolves the response based on the provide event and decorator routes

        ## Internals

        Request processing chain is triggered by a Route object being called _(`_call_route` -> `__call__`)_:

        1. **When a route is matched**
          1.1. Exception handlers _(if any exception bubbled up and caught)_
          1.2. Global middlewares _(before, and after on the way back)_
          1.3. Path level middleware _(before, and after on the way back)_
          1.4. Middleware adapter to ensure Response is homogenous (_registered_api_adapter)
          1.5. Run actual route
        2. **When a route is NOT matched**
          2.1. Exception handlers _(if any exception bubbled up and caught)_
          2.2. Global middlewares _(before, and after on the way back)_
          2.3. Path level middleware _(before, and after on the way back)_
          2.4. Middleware adapter to ensure Response is homogenous (_registered_api_adapter)
          2.5. Run 404 route handler
        3. **When a route is a pre-flight CORS (often not matched)**
          3.1. Exception handlers _(if any exception bubbled up and caught)_
          3.2. Global middlewares _(before, and after on the way back)_
          3.3. Path level middleware _(before, and after on the way back)_
          3.4. Middleware adapter to ensure Response is homogenous (_registered_api_adapter)
          3.5. Return 204 with appropriate CORS headers
        4. **When a route is matched with Data Validation enabled**
          4.1. Exception handlers _(if any exception bubbled up and caught)_
          4.2. Data Validation middleware _(before, and after on the way back)_
          4.3. Global middlewares _(before, and after on the way back)_
          4.4. Path level middleware _(before, and after on the way back)_
          4.5. Middleware adapter to ensure Response is homogenous (_registered_api_adapter)
          4.6. Run actual route

        Parameters
        ----------
        event: dict[str, Any]
            Event
        context: LambdaContext
            Lambda context
        Returns
        -------
        dict
            Returns the dict response
        """
        if isinstance(event, BaseProxyEvent):
            warnings.warn(
                "You don't need to serialize event to Event Source Data Class when using Event Handler; "
                "see issue #1152",
                stacklevel=2,
            )
            event = event.raw_event

        if self._debug:
            print(self._serializer(event))

        # Populate router(s) dependencies without keeping a reference to each registered router
        BaseRouter.current_event = self._to_proxy_event(event)
        BaseRouter.lambda_context = context

        response = self._resolve().build(self.current_event, self._cors)

        # Debug print Processed Middlewares
        if self._debug:
            print("\nProcessed Middlewares:")
            print("======================")
            print("\n".join(self.processed_stack_frames))
            print("======================")

        self.clear_context()

        return response

    def __call__(self, event, context) -> Any:
        return self.resolve(event, context)

    def _create_route_key(self, item: str, rule: str):
        route_key = item + rule
        if route_key in self._route_keys:
            warnings.warn(
                f"A route like this was already registered. method: '{item}' rule: '{rule}'",
                stacklevel=2,
            )
        self._route_keys.append(route_key)

    def _get_base_path(self) -> str:
        raise NotImplementedError()

    @staticmethod
    def _has_debug(debug: bool | None = None) -> bool:
        # It might have been explicitly switched off (debug=False)
        return debug if debug is not None else powertools_dev_is_set()

    @staticmethod
    def _compile_regex(rule: str, base_regex: str = _ROUTE_REGEX):
        """Precompile regex pattern

        Logic
        -----

        1. Find any dynamic routes defined as <pattern>
            e.g. @app.get("/accounts/<account_id>")
        2. Create a new regex by substituting every dynamic route found as a named group (?P<group>),
        and match whole words only (word boundary) instead of a greedy match

            non-greedy example with word boundary

                rule: '/accounts/<account_id>'
                regex: r'/accounts/(?P<account_id>\\w+\\b)'

                value: /accounts/123/some_other_path
                account_id: 123

            greedy example without word boundary

                regex: r'/accounts/(?P<account_id>.+)'

                value: /accounts/123/some_other_path
                account_id: 123/some_other_path
        3. Compiles a regex and include start (^) and end ($) in between for an exact match

        NOTE: See #520 for context
        """
        rule_regex: str = re.sub(_DYNAMIC_ROUTE_PATTERN, _NAMED_GROUP_BOUNDARY_PATTERN, rule)
        return re.compile(base_regex.format(rule_regex))

    def _to_proxy_event(self, event: dict) -> BaseProxyEvent:  # noqa: PLR0911  # ignore many returns
        """Convert the event dict to the corresponding data class"""
        if self._proxy_type == ProxyEventType.APIGatewayProxyEvent:
            logger.debug("Converting event to API Gateway REST API contract")
            return APIGatewayProxyEvent(event)
        if self._proxy_type == ProxyEventType.APIGatewayProxyEventV2:
            logger.debug("Converting event to API Gateway HTTP API contract")
            return APIGatewayProxyEventV2(event)
        if self._proxy_type == ProxyEventType.BedrockAgentEvent:
            logger.debug("Converting event to Bedrock Agent contract")
            return BedrockAgentEvent(event)
        if self._proxy_type == ProxyEventType.LambdaFunctionUrlEvent:
            logger.debug("Converting event to Lambda Function URL contract")
            return LambdaFunctionUrlEvent(event)
        if self._proxy_type == ProxyEventType.VPCLatticeEvent:
            logger.debug("Converting event to VPC Lattice contract")
            return VPCLatticeEvent(event)
        if self._proxy_type == ProxyEventType.VPCLatticeEventV2:
            logger.debug("Converting event to VPC LatticeV2 contract")
            return VPCLatticeEventV2(event)
        logger.debug("Converting event to ALB contract")
        return ALBEvent(event)

    def _resolve(self) -> ResponseBuilder:
        """Resolves the response or return the not found response"""
        method = self.current_event.http_method.upper()
        path = self._remove_prefix(self.current_event.path)

        registered_routes = self._static_routes + self._dynamic_routes

        for route in registered_routes:
            if method != route.method:
                continue
            match_results: Match | None = route.rule.match(path)
            if match_results:
                logger.debug("Found a registered route. Calling function")
                # Add matched Route reference into the Resolver context
                self.append_context(_route=route, _path=path)

                route_keys = self._convert_matches_into_route_keys(match_results)
                return self._call_route(route, route_keys)  # pass fn args

        return self._handle_not_found(method=method, path=path)

    def _remove_prefix(self, path: str) -> str:
        """Remove the configured prefix from the path"""
        if not isinstance(self._strip_prefixes, list):
            return path

        for prefix in self._strip_prefixes:
            if isinstance(prefix, str):
                if path == prefix:
                    return "/"

                if self._path_starts_with(path, prefix):
                    return path[len(prefix) :]

            if isinstance(prefix, Pattern):
                path = re.sub(prefix, "", path)

                # When using regexes, we might get into a point where everything is removed
                # from the string, so we check if it's empty and return /, since there's nothing
                # else to strip anymore.
                if not path:
                    return "/"

        return path

    def _convert_matches_into_route_keys(self, match: Match) -> dict[str, str]:
        """Converts the regex match into a dict of route keys"""
        return match.groupdict()

    @staticmethod
    def _path_starts_with(path: str, prefix: str):
        """Returns true if the `path` starts with a prefix plus a `/`"""
        if not isinstance(prefix, str) or prefix == "":
            return False

        return path.startswith(f"{prefix}/")

    def _handle_not_found(self, method: str, path: str) -> ResponseBuilder:
        """Called when no matching route was found and includes support for the cors preflight response"""
        logger.debug(f"No match found for path {path} and method {method}")

        def not_found_handler():
            """Route handler for 404s

            It handles in the following order:

            1. Pre-flight CORS requests (OPTIONS)
            2. Detects and calls custom HTTP 404 handler
            3. Returns standard 404 along with CORS headers

            Returns
            -------
            Response
                HTTP 404 response
            """
            _headers: dict[str, Any] = {}

            # Pre-flight request? Return immediately to avoid browser error
            if self._cors and method == "OPTIONS":
                logger.debug("Pre-flight request detected. Returning CORS with empty response")
                _headers["Access-Control-Allow-Methods"] = CORSConfig.build_allow_methods(self._cors_methods)

                return Response(status_code=204, content_type=None, headers=_headers, body="")

            # Customer registered 404 route? Call it.
            custom_not_found_handler = self._lookup_exception_handler(NotFoundError)
            if custom_not_found_handler:
                return custom_not_found_handler(NotFoundError())

            # No CORS and no custom 404 fn? Default response
            return Response(
                status_code=HTTPStatus.NOT_FOUND.value,
                content_type=content_types.APPLICATION_JSON,
                headers=_headers,
                body={"statusCode": HTTPStatus.NOT_FOUND.value, "message": "Not found"},
            )

        # We create a route to trigger entire request chain (middleware+exception handlers)
        route = Route(
            rule=self._compile_regex(r".*"),
            method=method,
            path=path,
            func=not_found_handler,
            cors=self._cors_enabled,
            compress=False,
        )

        # Add matched Route reference into the Resolver context
        self.append_context(_route=route, _path=path)

        # Kick-off request chain:
        # -> exception_handlers()
        # --> middlewares()
        # ---> not_found_route()
        return self._call_route(route=route, route_arguments={})

    def _call_route(self, route: Route, route_arguments: dict[str, str]) -> ResponseBuilder:
        """Actually call the matching route with any provided keyword arguments."""
        try:
            # Reset Processed stack for Middleware (for debugging purposes)
            self._reset_processed_stack()

            return self._response_builder_class(
                response=self._to_response(
                    route(router_middlewares=self._router_middlewares, app=self, route_arguments=route_arguments),
                ),
                serializer=self._serializer,
                route=route,
            )
        except Exception as exc:
            # If exception is handled then return the response builder to reduce noise
            response_builder = self._call_exception_handler(exc, route)
            if response_builder:
                return response_builder

            logger.exception(exc)
            if self._debug:
                # If the user has turned on debug mode,
                # we'll let the original exception propagate, so
                # they get more information about what went wrong.
                return self._response_builder_class(
                    response=Response(
                        status_code=500,
                        content_type=content_types.TEXT_PLAIN,
                        body="".join(traceback.format_exc()),
                    ),
                    serializer=self._serializer,
                    route=route,
                )

            raise

    def not_found(self, func: Callable | None = None):
        if func is None:
            return self.exception_handler(NotFoundError)
        return self.exception_handler(NotFoundError)(func)

    def exception_handler(self, exc_class: type[Exception] | list[type[Exception]]):
        def register_exception_handler(func: Callable):
            if isinstance(exc_class, list):  # pragma: no cover
                for exp in exc_class:
                    self._exception_handlers[exp] = func
            else:
                self._exception_handlers[exc_class] = func
            return func

        return register_exception_handler

    def _lookup_exception_handler(self, exp_type: type) -> Callable | None:
        # Use "Method Resolution Order" to allow for matching against a base class
        # of an exception
        for cls in exp_type.__mro__:
            if cls in self._exception_handlers:
                return self._exception_handlers[cls]
        return None

    def _call_exception_handler(self, exp: Exception, route: Route) -> ResponseBuilder | None:
        handler = self._lookup_exception_handler(type(exp))
        if handler:
            try:
                return self._response_builder_class(response=handler(exp), serializer=self._serializer, route=route)
            except ServiceError as service_error:
                exp = service_error

        if isinstance(exp, RequestValidationError):
            # For security reasons, we hide msg details (don't leak Python, Pydantic or file names)
            errors = [{"loc": e["loc"], "type": e["type"]} for e in exp.errors()]

            return self._response_builder_class(
                response=Response(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                    content_type=content_types.APPLICATION_JSON,
                    body={"statusCode": HTTPStatus.UNPROCESSABLE_ENTITY, "detail": errors},
                ),
                serializer=self._serializer,
                route=route,
            )

        # OpenAPIValidationMiddleware will only raise ResponseValidationError when
        # 'self._response_validation_error_http_code' is not None
        if isinstance(exp, ResponseValidationError):
            http_code = self._response_validation_error_http_code
            errors = [{"loc": e["loc"], "type": e["type"]} for e in exp.errors()]
            return self._response_builder_class(
                response=Response(
                    status_code=http_code.value,
                    content_type=content_types.APPLICATION_JSON,
                    body={"statusCode": self._response_validation_error_http_code, "detail": errors},
                ),
                serializer=self._serializer,
                route=route,
            )

        if isinstance(exp, ServiceError):
            return self._response_builder_class(
                response=Response(
                    status_code=exp.status_code,
                    content_type=content_types.APPLICATION_JSON,
                    body={"statusCode": exp.status_code, "message": exp.msg},
                ),
                serializer=self._serializer,
                route=route,
            )

        return None

    def _to_response(self, result: dict | tuple | Response) -> Response:
        """Convert the route's result to a Response

         3 main result types are supported:

        - dict[str, Any]: Rest api response with just the dict to json stringify and content-type is set to
          application/json
        - tuple[dict, int]: Same dict handling as above but with the option of including a status code
        - Response: returned as is, and allows for more flexibility
        """
        status_code = HTTPStatus.OK
        if isinstance(result, Response):
            return result
        elif isinstance(result, tuple) and len(result) == 2:
            # Unpack result dict and status code from tuple
            result, status_code = result

        logger.debug("Simple response detected, serializing return before constructing final response")
        return Response(
            status_code=status_code,
            content_type=content_types.APPLICATION_JSON,
            body=result,
        )

    def include_router(self, router: Router, prefix: str | None = None) -> None:
        """Adds all routes and context defined in a router

        Parameters
        ----------
        router : Router
            The Router containing a list of routes to be registered after the existing routes
        prefix : str, optional
            An optional prefix to be added to the originally defined rule
        """

        # Add reference to parent ApiGatewayResolver to support use cases where people subclass it to add custom logic
        router.api_resolver = self

        logger.debug("Merging App context with Router context")
        self.context.update(**router.context)

        logger.debug("Appending Router middlewares into App middlewares.")
        self._router_middlewares = self._router_middlewares + router._router_middlewares

        logger.debug("Appending Router exception_handler into App exception_handler.")
        self._exception_handlers.update(router._exception_handlers)

        # use pointer to allow context clearance after event is processed e.g., resolve(evt, ctx)
        router.context = self.context

        # Iterate through the routes defined in the router to configure and apply middlewares for each route
        for route, func in router._routes.items():
            new_route = route

            if prefix:
                rule = route[0]
                rule = prefix if rule == "/" else f"{prefix}{rule}"
                new_route = (rule, *route[1:])

            # Middlewares are stored by route separately - must grab them to include
            # Middleware store the route without prefix, so we must not include prefix when grabbing
            middlewares = router._routes_with_middleware.get(route)

            # Need to use "type: ignore" here since mypy does not like a named parameter after
            # tuple expansion since may cause duplicate named parameters in the function signature.
            # In this case this is not possible since the tuple expansion is from a hashable source
            # and the `middlewares` list is a non-hashable structure so will never be included.
            # Still need to ignore for mypy checks or will cause failures (false-positive)
            self.route(*new_route, middlewares=middlewares)(func)  # type: ignore

    @staticmethod
    def _get_fields_from_routes(routes: Sequence[Route]) -> list[ModelField]:
        """
        Returns a list of fields from the routes
        """

        from aws_lambda_powertools.event_handler.openapi.compat import ModelField
        from aws_lambda_powertools.event_handler.openapi.dependant import (
            get_flat_params,
        )

        body_fields_from_routes: list[ModelField] = []
        responses_from_routes: list[ModelField] = []
        request_fields_from_routes: list[ModelField] = []

        for route in routes:
            if route.body_field:
                if not isinstance(route.body_field, ModelField):
                    raise AssertionError("A request body myst be a Pydantic Field")
                body_fields_from_routes.append(route.body_field)

            params = get_flat_params(route.dependant)
            request_fields_from_routes.extend(params)

            if route.dependant.return_param:
                responses_from_routes.append(route.dependant.return_param)

            if route.dependant.response_extra_models:
                responses_from_routes.extend(route.dependant.response_extra_models)

        return list(
            responses_from_routes + request_fields_from_routes + body_fields_from_routes,
        )


class Router(BaseRouter):
    """Router helper class to allow splitting ApiGatewayResolver into multiple files"""

    def __init__(self):
        self._routes: dict[tuple, Callable] = {}
        self._routes_with_middleware: dict[tuple, list[Callable]] = {}
        self.api_resolver: BaseRouter | None = None
        self.context = {}  # early init as customers might add context before event resolution
        self._exception_handlers: dict[type, Callable] = {}

    def route(
        self,
        rule: str,
        method: str | list[str] | tuple[str],
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str | None = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> Callable[[AnyCallableT], AnyCallableT]:
        def register_route(func: AnyCallableT) -> AnyCallableT:
            # All dict keys needs to be hashable. So we'll need to do some conversions:
            methods = (method,) if isinstance(method, str) else tuple(method)
            frozen_responses = _FrozenDict(responses) if responses else None
            frozen_tags = frozenset(tags) if tags else None
            frozen_security = _FrozenListDict(security) if security else None
            frozen_openapi_extensions = _FrozenDict(openapi_extensions) if openapi_extensions else None

            route_key = (
                rule,
                methods,
                cors,
                compress,
                cache_control,
                summary,
                description,
                frozen_responses,
                response_description,
                frozen_tags,
                operation_id,
                include_in_schema,
                frozen_security,
                frozen_openapi_extensions,
                deprecated,
            )

            # Collate Middleware for routes
            if middlewares is not None:
                for handler in middlewares:
                    if self._routes_with_middleware.get(route_key) is None:
                        self._routes_with_middleware[route_key] = [handler]
                    else:
                        self._routes_with_middleware[route_key].append(handler)
            else:
                self._routes_with_middleware[route_key] = []

            self._routes[route_key] = func

            return func

        return register_route

    def exception_handler(self, exc_class: type[Exception] | list[type[Exception]]):
        def register_exception_handler(func: Callable):
            if isinstance(exc_class, list):
                for exp in exc_class:
                    self._exception_handlers[exp] = func
            else:
                self._exception_handlers[exc_class] = func
            return func

        return register_exception_handler


class APIGatewayRestResolver(ApiGatewayResolver):
    """Amazon API Gateway REST and HTTP API v1 payload resolver"""

    current_event: APIGatewayProxyEvent

    def __init__(
        self,
        cors: CORSConfig | None = None,
        debug: bool | None = None,
        serializer: Callable[[dict], str] | None = None,
        strip_prefixes: list[str | Pattern] | None = None,
        enable_validation: bool = False,
        response_validation_error_http_code: HTTPStatus | int | None = None,
    ):
        """Amazon API Gateway REST and HTTP API v1 payload resolver"""
        super().__init__(
            ProxyEventType.APIGatewayProxyEvent,
            cors,
            debug,
            serializer,
            strip_prefixes,
            enable_validation,
            response_validation_error_http_code,
        )

    def _get_base_path(self) -> str:
        # 3 different scenarios:
        #
        # 1. SAM local: even though a stage variable is sent to the Lambda function, it's not used in the path
        # 2. API Gateway REST API: stage variable is used in the path
        # 3. API Gateway REST Custom Domain: stage variable is not used in the path
        #
        # To solve the 3 scenarios, we try to match the beginning of the path with the stage variable
        stage = self.current_event.request_context.stage
        if stage and stage != "$default" and self.current_event.request_context.path.startswith(f"/{stage}"):
            return f"/{stage}"
        return ""

    # override route to ignore trailing "/" in routes for REST API
    def route(
        self,
        rule: str,
        method: str | list[str] | tuple[str],
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> Callable[[AnyCallableT], AnyCallableT]:
        # NOTE: see #1552 for more context.
        return super().route(
            rule.rstrip("/"),
            method,
            cors,
            compress,
            cache_control,
            summary,
            description,
            responses,
            response_description,
            tags,
            operation_id,
            include_in_schema,
            security,
            openapi_extensions,
            deprecated,
            middlewares,
        )

    # Override _compile_regex to exclude trailing slashes for route resolution
    @staticmethod
    def _compile_regex(rule: str, base_regex: str = _ROUTE_REGEX):
        return super(APIGatewayRestResolver, APIGatewayRestResolver)._compile_regex(rule, "^{}/*$")


class APIGatewayHttpResolver(ApiGatewayResolver):
    """Amazon API Gateway HTTP API v2 payload resolver"""

    current_event: APIGatewayProxyEventV2

    def __init__(
        self,
        cors: CORSConfig | None = None,
        debug: bool | None = None,
        serializer: Callable[[dict], str] | None = None,
        strip_prefixes: list[str | Pattern] | None = None,
        enable_validation: bool = False,
        response_validation_error_http_code: HTTPStatus | int | None = None,
    ):
        """Amazon API Gateway HTTP API v2 payload resolver"""
        super().__init__(
            ProxyEventType.APIGatewayProxyEventV2,
            cors,
            debug,
            serializer,
            strip_prefixes,
            enable_validation,
            response_validation_error_http_code,
        )

    def _get_base_path(self) -> str:
        # 3 different scenarios:
        #
        # 1. SAM local: even though a stage variable is sent to the Lambda function, it's not used in the path
        # 2. API Gateway HTTP API: stage variable is used in the path
        # 3. API Gateway HTTP Custom Domain: stage variable is not used in the path
        #
        # To solve the 3 scenarios, we try to match the beginning of the path with the stage variable
        stage = self.current_event.request_context.stage
        if stage and stage != "$default" and self.current_event.request_context.http.path.startswith(f"/{stage}"):
            return f"/{stage}"
        return ""


class ALBResolver(ApiGatewayResolver):
    """Amazon Application Load Balancer (ALB) resolver"""

    current_event: ALBEvent

    def __init__(
        self,
        cors: CORSConfig | None = None,
        debug: bool | None = None,
        serializer: Callable[[dict], str] | None = None,
        strip_prefixes: list[str | Pattern] | None = None,
        enable_validation: bool = False,
        response_validation_error_http_code: HTTPStatus | int | None = None,
    ):
        """Amazon Application Load Balancer (ALB) resolver"""
        super().__init__(
            ProxyEventType.ALBEvent,
            cors,
            debug,
            serializer,
            strip_prefixes,
            enable_validation,
            response_validation_error_http_code,
        )

    def _get_base_path(self) -> str:
        # ALB doesn't have a stage variable, so we just return an empty string
        return ""

    @override
    def _to_response(self, result: dict | tuple | Response) -> Response:
        """Convert the route's result to a Response

        ALB requires a non-null body otherwise it converts as HTTP 5xx

         3 main result types are supported:

        - Dict[str, Any]: Rest api response with just the Dict to json stringify and content-type is set to
          application/json
        - Tuple[dict, int]: Same dict handling as above but with the option of including a status code
        - Response: returned as is, and allows for more flexibility
        """

        # NOTE: Minor override for early return on Response with null body for ALB
        if isinstance(result, Response) and result.body is None:
            logger.debug("ALB doesn't allow None responses; converting to empty string")
            result.body = ""

        return super()._to_response(result)
