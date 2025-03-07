from __future__ import annotations

import dataclasses
import json
import logging
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable, Mapping, MutableMapping, Sequence

from pydantic import BaseModel

from aws_lambda_powertools.event_handler.middlewares import BaseMiddlewareHandler
from aws_lambda_powertools.event_handler.openapi.compat import (
    _model_dump,
    _normalize_errors,
    _regenerate_error_with_loc,
    get_missing_field_error,
)
from aws_lambda_powertools.event_handler.openapi.dependant import is_scalar_field
from aws_lambda_powertools.event_handler.openapi.encoders import jsonable_encoder
from aws_lambda_powertools.event_handler.openapi.exceptions import RequestValidationError
from aws_lambda_powertools.event_handler.openapi.params import Param

if TYPE_CHECKING:
    from aws_lambda_powertools.event_handler import Response
    from aws_lambda_powertools.event_handler.api_gateway import Route
    from aws_lambda_powertools.event_handler.middlewares import NextMiddleware
    from aws_lambda_powertools.event_handler.openapi.compat import ModelField
    from aws_lambda_powertools.event_handler.openapi.types import IncEx
    from aws_lambda_powertools.event_handler.types import EventHandlerInstance

logger = logging.getLogger(__name__)


class OpenAPIValidationMiddleware(BaseMiddlewareHandler):
    """
    OpenAPIValidationMiddleware is a middleware that validates the request against the OpenAPI schema defined by the
    Lambda handler. It also validates the response against the OpenAPI schema defined by the Lambda handler. It
    should not be used directly, but rather through the `enable_validation` parameter of the `ApiGatewayResolver`.

    Example
    --------

    ```python
    from pydantic import BaseModel

    from aws_lambda_powertools.event_handler.api_gateway import (
        APIGatewayRestResolver,
    )

    class Todo(BaseModel):
      name: str

    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/todos")
    def get_todos(): list[Todo]:
      return [Todo(name="hello world")]
    ```
    """

    def __init__(self, validation_serializer: Callable[[Any], str] | None = None):
        """
        Initialize the OpenAPIValidationMiddleware.

        Parameters
        ----------
        validation_serializer : Callable, optional
            Optional serializer to use when serializing the response for validation.
            Use it when you have a custom type that cannot be serialized by the default jsonable_encoder.
        """
        self._validation_serializer = validation_serializer

    def handler(self, app: EventHandlerInstance, next_middleware: NextMiddleware) -> Response:
        logger.debug("OpenAPIValidationMiddleware handler")

        route: Route = app.context["_route"]

        values: dict[str, Any] = {}
        errors: list[Any] = []

        # Process path values, which can be found on the route_args
        path_values, path_errors = _request_params_to_args(
            route.dependant.path_params,
            app.context["_route_args"],
        )

        # Normalize query values before validate this
        query_string = _normalize_multi_query_string_with_param(
            app.current_event.resolved_query_string_parameters,
            route.dependant.query_params,
        )

        # Process query values
        query_values, query_errors = _request_params_to_args(
            route.dependant.query_params,
            query_string,
        )

        # Normalize header values before validate this
        headers = _normalize_multi_header_values_with_param(
            app.current_event.resolved_headers_field,
            route.dependant.header_params,
        )

        # Process header values
        header_values, header_errors = _request_params_to_args(
            route.dependant.header_params,
            headers,
        )

        values.update(path_values)
        values.update(query_values)
        values.update(header_values)
        errors += path_errors + query_errors + header_errors

        # Process the request body, if it exists
        if route.dependant.body_params:
            (body_values, body_errors) = _request_body_to_args(
                required_params=route.dependant.body_params,
                received_body=self._get_body(app),
            )
            values.update(body_values)
            errors.extend(body_errors)

        if errors:
            # Raise the validation errors
            raise RequestValidationError(_normalize_errors(errors))
        else:
            # Re-write the route_args with the validated values, and call the next middleware
            app.context["_route_args"] = values

            # Call the handler by calling the next middleware
            response = next_middleware(app)

            # Process the response
            return self._handle_response(route=route, response=response)

    def _handle_response(self, *, route: Route, response: Response):
        # Process the response body if it exists
        if response.body and response.is_json():
            response.body = self._serialize_response(
                field=route.dependant.return_param,
                response_content=response.body,
            )

        return response

    def _serialize_response(
        self,
        *,
        field: ModelField | None = None,
        response_content: Any,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> Any:
        """
        Serialize the response content according to the field type.
        """
        if field:
            errors: list[dict[str, Any]] = []
            value = _validate_field(field=field, value=response_content, loc=("response",), existing_errors=errors)
            if errors:
                raise RequestValidationError(errors=_normalize_errors(errors), body=response_content)

            if hasattr(field, "serialize"):
                return field.serialize(
                    value,
                    include=include,
                    exclude=exclude,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none,
                )
            return jsonable_encoder(
                value,
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                custom_serializer=self._validation_serializer,
            )
        else:
            # Just serialize the response content returned from the handler.
            return jsonable_encoder(response_content, custom_serializer=self._validation_serializer)

    def _prepare_response_content(
        self,
        res: Any,
        *,
        exclude_unset: bool,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> Any:
        """
        Prepares the response content for serialization.
        """
        if isinstance(res, BaseModel):
            return _model_dump(
                res,
                by_alias=True,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )
        elif isinstance(res, list):
            return [
                self._prepare_response_content(item, exclude_unset=exclude_unset, exclude_defaults=exclude_defaults)
                for item in res
            ]
        elif isinstance(res, dict):
            return {
                k: self._prepare_response_content(v, exclude_unset=exclude_unset, exclude_defaults=exclude_defaults)
                for k, v in res.items()
            }
        elif dataclasses.is_dataclass(res):
            return dataclasses.asdict(res)  # type: ignore[arg-type]
        return res

    def _get_body(self, app: EventHandlerInstance) -> dict[str, Any]:
        """
        Get the request body from the event, and parse it as JSON.
        """

        content_type = app.current_event.headers.get("content-type")
        if not content_type or content_type.strip().startswith("application/json"):
            try:
                return app.current_event.json_body
            except json.JSONDecodeError as e:
                raise RequestValidationError(
                    [
                        {
                            "type": "json_invalid",
                            "loc": ("body", e.pos),
                            "msg": "JSON decode error",
                            "input": {},
                            "ctx": {"error": e.msg},
                        },
                    ],
                    body=e.doc,
                ) from e
        else:
            raise NotImplementedError("Only JSON body is supported")


def _request_params_to_args(
    required_params: Sequence[ModelField],
    received_params: Mapping[str, Any],
) -> tuple[dict[str, Any], list[Any]]:
    """
    Convert the request params to a dictionary of values using validation, and returns a list of errors.
    """
    values = {}
    errors = []

    for field in required_params:
        field_info = field.field_info

        # To ensure early failure, we check if it's not an instance of Param.
        if not isinstance(field_info, Param):
            raise AssertionError(f"Expected Param field_info, got {field_info}")

        value = received_params.get(field.alias)

        loc = (field_info.in_.value, field.alias)

        # If we don't have a value, see if it's required or has a default
        if value is None:
            if field.required:
                errors.append(get_missing_field_error(loc=loc))
            else:
                values[field.name] = deepcopy(field.default)
            continue

        # Finally, validate the value
        values[field.name] = _validate_field(field=field, value=value, loc=loc, existing_errors=errors)

    return values, errors


def _request_body_to_args(
    required_params: list[ModelField],
    received_body: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Convert the request body to a dictionary of values using validation, and returns a list of errors.
    """
    values: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []

    received_body, field_alias_omitted = _get_embed_body(
        field=required_params[0],
        required_params=required_params,
        received_body=received_body,
    )

    for field in required_params:
        # This sets the location to:
        # { "user": { object } } if field.alias == user
        # { { object } if field_alias is omitted
        loc: tuple[str, ...] = ("body", field.alias)
        if field_alias_omitted:
            loc = ("body",)

        value: Any | None = None

        # Now that we know what to look for, try to get the value from the received body
        if received_body is not None:
            try:
                value = received_body.get(field.alias)
            except AttributeError:
                errors.append(get_missing_field_error(loc))
                continue

        # Determine if the field is required
        if value is None:
            if field.required:
                errors.append(get_missing_field_error(loc))
            else:
                values[field.name] = deepcopy(field.default)
            continue

        # MAINTENANCE: Handle byte and file fields

        # Finally, validate the value
        values[field.name] = _validate_field(field=field, value=value, loc=loc, existing_errors=errors)

    return values, errors


def _validate_field(
    *,
    field: ModelField,
    value: Any,
    loc: tuple[str, ...],
    existing_errors: list[dict[str, Any]],
):
    """
    Validate a field, and append any errors to the existing_errors list.
    """
    validated_value, errors = field.validate(value, value, loc=loc)

    if isinstance(errors, list):
        processed_errors = _regenerate_error_with_loc(errors=errors, loc_prefix=())
        existing_errors.extend(processed_errors)
    elif errors:
        existing_errors.append(errors)

    return validated_value


def _get_embed_body(
    *,
    field: ModelField,
    required_params: list[ModelField],
    received_body: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, bool]:
    field_info = field.field_info
    embed = getattr(field_info, "embed", None)

    # If the field is an embed, and the field alias is omitted, we need to wrap the received body in the field alias.
    field_alias_omitted = len(required_params) == 1 and not embed
    if field_alias_omitted:
        received_body = {field.alias: received_body}

    return received_body, field_alias_omitted


def _normalize_multi_query_string_with_param(
    query_string: dict[str, list[str]],
    params: Sequence[ModelField],
) -> dict[str, Any]:
    """
    Extract and normalize resolved_query_string_parameters

    Parameters
    ----------
    query_string: dict
        A dictionary containing the initial query string parameters.
    params: Sequence[ModelField]
        A sequence of ModelField objects representing parameters.

    Returns
    -------
    A dictionary containing the processed multi_query_string_parameters.
    """
    resolved_query_string: dict[str, Any] = query_string
    for param in filter(is_scalar_field, params):
        try:
            # if the target parameter is a scalar, we keep the first value of the query string
            # regardless if there are more in the payload
            resolved_query_string[param.alias] = query_string[param.alias][0]
        except KeyError:
            pass
    return resolved_query_string


def _normalize_multi_header_values_with_param(headers: MutableMapping[str, Any], params: Sequence[ModelField]):
    """
    Extract and normalize resolved_headers_field

    Parameters
    ----------
    headers: MutableMapping[str, Any]
        A dictionary containing the initial header parameters.
    params: Sequence[ModelField]
        A sequence of ModelField objects representing parameters.

    Returns
    -------
    A dictionary containing the processed headers.
    """
    if headers:
        for param in filter(is_scalar_field, params):
            try:
                if len(headers[param.alias]) == 1:
                    # if the target parameter is a scalar and the list contains only 1 element
                    # we keep the first value of the headers regardless if there are more in the payload
                    headers[param.alias] = headers[param.alias][0]
            except KeyError:
                pass
    return headers
