from __future__ import annotations

import base64
import dataclasses
import json
import logging
import warnings
from typing import TYPE_CHECKING, Any, Callable, Mapping, MutableMapping, Sequence, Union, cast
from urllib.parse import parse_qs

from pydantic import BaseModel
from typing_extensions import get_args, get_origin

from aws_lambda_powertools.event_handler.middlewares import BaseMiddlewareHandler
from aws_lambda_powertools.event_handler.openapi.compat import (
    _model_dump,
    _normalize_errors,
    _regenerate_error_with_loc,
    field_annotation_is_sequence,
    get_missing_field_error,
    lenient_issubclass,
)
from aws_lambda_powertools.event_handler.openapi.dependant import is_scalar_field
from aws_lambda_powertools.event_handler.openapi.encoders import jsonable_encoder
from aws_lambda_powertools.event_handler.openapi.exceptions import (
    RequestUnsupportedContentType,
    RequestValidationError,
    ResponseValidationError,
)
from aws_lambda_powertools.event_handler.openapi.params import Param, UploadFile
from aws_lambda_powertools.event_handler.openapi.types import UnionType

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo

    from aws_lambda_powertools.event_handler import Response
    from aws_lambda_powertools.event_handler.api_gateway import Route
    from aws_lambda_powertools.event_handler.middlewares import NextMiddleware
    from aws_lambda_powertools.event_handler.openapi.compat import ModelField
    from aws_lambda_powertools.event_handler.openapi.types import IncEx
    from aws_lambda_powertools.event_handler.types import EventHandlerInstance

logger = logging.getLogger(__name__)

# Constants
CONTENT_DISPOSITION_NAME_PARAM = "name="
APPLICATION_JSON_CONTENT_TYPE = "application/json"
APPLICATION_FORM_CONTENT_TYPE = "application/x-www-form-urlencoded"
MULTIPART_FORM_DATA_CONTENT_TYPE = "multipart/form-data"


class OpenAPIRequestValidationMiddleware(BaseMiddlewareHandler):
    """
    OpenAPI request validation middleware - validates only incoming requests.

    This middleware should be used first in the middleware chain to validate
    requests before they reach user middlewares.
    """

    def __init__(self):
        """Initialize the request validation middleware."""
        pass

    def handler(self, app: EventHandlerInstance, next_middleware: NextMiddleware) -> Response:
        logger.debug("OpenAPIRequestValidationMiddleware handler")

        route: Route = app.context["_route"]

        values: dict[str, Any] = {}
        errors: list[Any] = []

        # Process path values, which can be found on the route_args
        path_values, path_errors = _request_params_to_args(
            route.dependant.path_params,
            app.context["_route_args"],
        )

        # Normalize query values before validate this
        query_string = _normalize_multi_params(
            app.current_event.resolved_query_string_parameters,
            route.dependant.query_params,
        )

        # Process query values
        query_values, query_errors = _request_params_to_args(
            route.dependant.query_params,
            query_string,
        )

        # Normalize header values before validate this
        headers = _normalize_multi_params(
            app.current_event.resolved_headers_field,
            route.dependant.header_params,
        )

        # Process header values
        header_values, header_errors = _request_params_to_args(
            route.dependant.header_params,
            headers,
        )

        # Process cookie values
        cookie_values, cookie_errors = _request_params_to_args(
            route.dependant.cookie_params,
            app.current_event.resolved_cookies_field,
        )

        values.update(path_values)
        values.update(query_values)
        values.update(header_values)
        values.update(cookie_values)
        errors += path_errors + query_errors + header_errors + cookie_errors

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

        # Re-write the route_args with the validated values
        app.context["_route_args"] = values

        # Call the next middleware
        return next_middleware(app)

    def _get_body(self, app: EventHandlerInstance) -> dict[str, Any]:
        """
        Get the request body from the event, and parse it according to content type.
        """
        content_type = app.current_event.headers.get("content-type", "").strip()

        # Handle JSON content
        if not content_type or content_type.startswith(APPLICATION_JSON_CONTENT_TYPE):
            return self._parse_json_data(app)

        # Handle URL-encoded form data
        elif content_type.startswith(APPLICATION_FORM_CONTENT_TYPE):
            return self._parse_form_data(app)

        # Handle multipart/form-data (file uploads)
        elif content_type.startswith(MULTIPART_FORM_DATA_CONTENT_TYPE):
            return self._parse_multipart_data(app, content_type)

        else:
            raise RequestUnsupportedContentType(
                "Unsupported content type",
                errors=[
                    {
                        "type": "unsupported_content_type",
                        "loc": ("body",),
                        "msg": f"Unsupported content type: {content_type}",
                        "input": {},
                        "ctx": {},
                    },
                ],
            )

    def _parse_json_data(self, app: EventHandlerInstance) -> dict[str, Any]:
        """Parse JSON data from the request body."""
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

    def _parse_form_data(self, app: EventHandlerInstance) -> dict[str, Any]:
        """Parse URL-encoded form data from the request body."""
        try:
            body = app.current_event.decoded_body or ""
            # NOTE: Keep values as lists; we'll normalize per-field later based on the expected type.
            # This avoids breaking List[...] fields when only a single value is provided.
            parsed = parse_qs(body, keep_blank_values=True)
            return parsed

        except Exception as e:  # pragma: no cover
            raise RequestValidationError(  # pragma: no cover
                [
                    {
                        "type": "form_invalid",
                        "loc": ("body",),
                        "msg": "Form data parsing error",
                        "input": {},
                        "ctx": {"error": str(e)},
                    },
                ],
            ) from e

    def _parse_multipart_data(self, app: EventHandlerInstance, content_type: str) -> dict[str, Any]:
        """Parse multipart/form-data from the request body (file uploads)."""
        try:
            # Extract the boundary from the content-type header
            boundary = _extract_multipart_boundary(content_type)
            if not boundary:
                raise ValueError("Missing boundary in multipart/form-data content-type header")

            # Get raw body bytes
            raw_body = app.current_event.body or ""
            if app.current_event.is_base64_encoded:
                body_bytes = base64.b64decode(raw_body)
            else:
                warnings.warn(
                    "Received multipart/form-data without base64 encoding. "
                    "Binary file uploads may be corrupted. "
                    "If using API Gateway REST API (v1), configure Binary Media Types "
                    "to include 'multipart/form-data'. "
                    "See: https://docs.aws.amazon.com/apigateway/latest/developerguide/"
                    "api-gateway-payload-encodings.html",
                    stacklevel=2,
                )
                # Use latin-1 to preserve all byte values (0-255) since the body
                # may contain raw binary data that isn't valid UTF-8
                body_bytes = raw_body.encode("latin-1")

            return _parse_multipart_body(body_bytes, boundary)

        except ValueError:
            raise
        except Exception as e:
            raise RequestValidationError(
                [
                    {
                        "type": "multipart_invalid",
                        "loc": ("body",),
                        "msg": "Multipart form data parsing error",
                        "input": {},
                        "ctx": {"error": str(e)},
                    },
                ],
            ) from e


class OpenAPIResponseValidationMiddleware(BaseMiddlewareHandler):
    """
    OpenAPI response validation middleware - validates only outgoing responses.

    This middleware should be used last in the middleware chain to validate
    responses only from route handlers, not from user middlewares.
    """

    def __init__(
        self,
        validation_serializer: Callable[[Any], str] | None = None,
        has_response_validation_error: bool = False,
    ):
        """
        Initialize the response validation middleware.

        Parameters
        ----------
        validation_serializer : Callable, optional
            Optional serializer to use when serializing the response for validation.
            Use it when you have a custom type that cannot be serialized by the default jsonable_encoder.

        has_response_validation_error: bool, optional
            Optional flag used to distinguish between payload and validation errors.
            By setting this flag to True, ResponseValidationError will be raised if response could not be validated.
        """
        self._validation_serializer = validation_serializer
        self._has_response_validation_error = has_response_validation_error

    def handler(self, app: EventHandlerInstance, next_middleware: NextMiddleware) -> Response:
        logger.debug("OpenAPIResponseValidationMiddleware handler")

        route: Route = app.context["_route"]

        # Call the next middleware (should be the route handler)
        response = next_middleware(app)

        # Process the response
        return self._handle_response(route=route, response=response)

    def _handle_response(self, *, route: Route, response: Response):
        field = route.dependant.return_param

        if field is None:
            if not response.is_json():
                return response
            else:
                # JSON serialize the body without validation
                response.body = jsonable_encoder(response.body, custom_serializer=self._validation_serializer)
        else:
            response.body = self._serialize_response_with_validation(
                field=field,
                response_content=response.body,
                has_route_custom_response_validation=route.custom_response_validation_http_code is not None,
            )

        return response

    def _serialize_response_with_validation(
        self,
        *,
        field: ModelField,
        response_content: Any,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        has_route_custom_response_validation: bool = False,
    ) -> Any:
        """
        Serialize the response content according to the field type.
        """
        errors: list[dict[str, Any]] = []
        value = _validate_field(field=field, value=response_content, loc=("response",), existing_errors=errors)
        if errors:
            # route-level validation must take precedence over app-level
            if has_route_custom_response_validation:
                raise ResponseValidationError(
                    errors=_normalize_errors(errors),
                    body=response_content,
                    source="route",
                )
            if self._has_response_validation_error:
                raise ResponseValidationError(errors=_normalize_errors(errors), body=response_content, source="app")

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
        if isinstance(res, BaseModel):  # pragma: no cover
            return _model_dump(  # pragma: no cover
                res,
                by_alias=True,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )
        elif isinstance(res, list):  # pragma: no cover
            return [  # pragma: no cover
                self._prepare_response_content(item, exclude_unset=exclude_unset, exclude_defaults=exclude_defaults)
                for item in res
            ]
        elif isinstance(res, dict):  # pragma: no cover
            return {  # pragma: no cover
                k: self._prepare_response_content(v, exclude_unset=exclude_unset, exclude_defaults=exclude_defaults)
                for k, v in res.items()
            }
        elif dataclasses.is_dataclass(res):  # pragma: no cover
            return dataclasses.asdict(res)  # type: ignore[arg-type] # pragma: no cover
        return res  # pragma: no cover


def _request_params_to_args(
    required_params: Sequence[ModelField],
    received_params: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Convert the request params to a dictionary of values using validation, and returns a list of errors.
    """
    values: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []

    for field in required_params:
        field_info = field.field_info

        # To ensure early failure, we check if it's not an instance of Param.
        if not isinstance(field_info, Param):
            raise AssertionError(f"Expected Param field_info, got {field_info}")

        loc = (field_info.in_.value, field.alias)
        value = received_params.get(field.alias)

        # If we don't have a value, see if it's required or has a default
        if value is None:
            _handle_missing_field_value(field, values, errors, loc)
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
        loc = _get_body_field_location(field, field_alias_omitted)
        value = _extract_field_value_from_body(field, received_body, loc, errors)

        # If we don't have a value, see if it's required or has a default
        if value is None:
            _handle_missing_field_value(field, values, errors, loc)
            continue

        value = _normalize_field_value(value=value, field_info=field.field_info)

        # UploadFile objects bypass Pydantic validation — they're already constructed
        if isinstance(value, UploadFile):
            values[field.name] = value
        else:
            values[field.name] = _validate_field(field=field, value=value, loc=loc, existing_errors=errors)

    return values, errors


def _get_body_field_location(field: ModelField, field_alias_omitted: bool) -> tuple[str, ...]:
    """Get the location tuple for a body field based on whether the field alias is omitted."""
    if field_alias_omitted:
        return ("body",)
    return ("body", field.alias)


def _extract_field_value_from_body(
    field: ModelField,
    received_body: dict[str, Any] | None,
    loc: tuple[str, ...],
    errors: list[dict[str, Any]],
) -> Any | None:
    """Extract field value from the received body, handling potential AttributeError."""
    if received_body is None:
        return None

    try:
        return received_body.get(field.alias)
    except AttributeError:
        errors.append(get_missing_field_error(loc))
        return None


def _handle_missing_field_value(
    field: ModelField,
    values: dict[str, Any],
    errors: list[dict[str, Any]],
    loc: tuple[str, ...],
) -> None:
    """Handle the case when a field value is missing."""
    if field.required:
        errors.append(get_missing_field_error(loc))
    else:
        values[field.name] = field.get_default()


def _is_or_contains_sequence(annotation: Any) -> bool:
    """
    Check if annotation is a sequence or Union/RootModel containing a sequence.

    This function handles complex type annotations like:
    - List[Model] - direct sequence
    - Union[Model, List[Model]] - checks if any Union member is a sequence
    - Optional[List[Model]] - Union[List[Model], None]
    - RootModel[List[Model]] - checks if the RootModel wraps a sequence
    - Optional[RootModel[List[Model]]] - Union member that is a RootModel
    - RootModel[Union[Model, List[Model]]] - RootModel wrapping a Union with a sequence
    """
    # Direct sequence check
    if field_annotation_is_sequence(annotation):
        return True

    # Check Union members — recurse so we catch RootModel inside Union
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        for arg in get_args(annotation):
            if _is_or_contains_sequence(arg):
                return True

    # Check if it's a RootModel wrapping a sequence (or Union containing a sequence)
    if lenient_issubclass(annotation, BaseModel) and getattr(annotation, "__pydantic_root_model__", False):
        if hasattr(annotation, "model_fields") and "root" in annotation.model_fields:
            root_annotation = annotation.model_fields["root"].annotation
            return _is_or_contains_sequence(root_annotation)

    return False


def _normalize_field_value(value: Any, field_info: FieldInfo) -> Any:
    """Normalize field value, converting lists to single values for non-sequence fields."""
    # When annotation is bytes but value is UploadFile, extract raw content
    if isinstance(value, UploadFile) and field_info.annotation is bytes:
        return value.content

    if _is_or_contains_sequence(field_info.annotation):
        return value
    elif isinstance(value, list) and value:
        return value[0]

    return value


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
    validated_value, errors = field.validate(value=value, loc=loc)

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


def _normalize_multi_params(
    input_dict: MutableMapping[str, Any],
    params: Sequence[ModelField],
) -> MutableMapping[str, Any]:
    """
    Extract and normalize query string or header parameters with Pydantic model support.

    Parameters
    ----------
    input_dict: MutableMapping[str, Any]
        A dictionary containing the initial query string or header parameters.
    params: Sequence[ModelField]
        A sequence of ModelField objects representing parameters.

    Returns
    -------
    MutableMapping[str, Any]
        A dictionary containing the processed parameters with normalized values.
    """
    for param in params:
        if is_scalar_field(param):
            _process_scalar_param(input_dict, param)
        elif lenient_issubclass(param.field_info.annotation, BaseModel):
            _process_model_param(input_dict, param)
    return input_dict


def _process_scalar_param(input_dict: MutableMapping[str, Any], param: ModelField) -> None:
    """Process a scalar parameter by normalizing single-item lists."""
    try:
        value = input_dict[param.alias]
        if isinstance(value, list) and len(value) == 1:
            input_dict[param.alias] = value[0]
    except KeyError:
        pass


def _process_model_param(input_dict: MutableMapping[str, Any], param: ModelField) -> None:
    """Process a Pydantic model parameter by extracting model fields."""
    model_class = cast(type[BaseModel], param.field_info.annotation)

    model_data = {}
    for field_name, field_info in model_class.model_fields.items():
        field_alias = field_info.alias or field_name
        value = _get_param_value(input_dict, field_alias, field_name, model_class)

        if value is not None:
            model_data[field_alias] = _normalize_field_value(value=value, field_info=field_info)

    input_dict[param.alias] = model_data


def _get_param_value(
    input_dict: MutableMapping[str, Any],
    field_alias: str,
    field_name: str,
    model_class: type[BaseModel],
) -> Any:
    """Get parameter value, checking both alias and field name if needed."""
    value = input_dict.get(field_alias)
    if value is not None:
        return value

    if model_class.model_config.get("validate_by_name") or model_class.model_config.get("populate_by_name"):
        value = input_dict.get(field_name)

    return value


def _extract_multipart_boundary(content_type: str) -> str | None:
    """Extract the boundary string from a multipart/form-data content-type header."""
    for segment in content_type.split(";"):
        stripped = segment.strip()
        if stripped.startswith("boundary="):
            boundary = stripped[len("boundary=") :]
            # Remove optional quotes around boundary
            if boundary.startswith('"') and boundary.endswith('"'):
                boundary = boundary[1:-1]
            return boundary
    return None


def _parse_multipart_body(body: bytes, boundary: str) -> dict[str, Any]:
    """
    Parse a multipart/form-data body into a dict of field names to values.

    File fields get bytes values; regular form fields get string values.
    Multiple values for the same field name are collected into lists.
    """
    delimiter = f"--{boundary}".encode()
    end_delimiter = f"--{boundary}--".encode()

    result: dict[str, Any] = {}

    # Split body by the boundary delimiter
    raw_parts = body.split(delimiter)

    for raw_part in raw_parts:
        # Skip the preamble (before first boundary) and epilogue (after closing boundary)
        if not raw_part or raw_part.strip() == b"" or raw_part.strip() == b"--":
            continue

        # Remove the end delimiter marker if present
        chunk = raw_part
        if chunk.endswith(end_delimiter):
            chunk = chunk[: -len(end_delimiter)]

        # Strip leading \r\n
        if chunk.startswith(b"\r\n"):
            chunk = chunk[2:]

        # Strip trailing \r\n
        if chunk.endswith(b"\r\n"):
            chunk = chunk[:-2]

        # Split headers from body at the double CRLF
        header_end = chunk.find(b"\r\n\r\n")
        if header_end == -1:
            continue

        header_section = chunk[:header_end].decode("utf-8")
        body_section = chunk[header_end + 4 :]

        # Parse Content-Disposition to get the field name and optional filename
        field_name = None
        filename = None
        content_type_header = None

        for header_line in header_section.split("\r\n"):
            header_lower = header_line.lower()
            if header_lower.startswith("content-disposition:"):
                field_name = _extract_header_param(header_line, "name")
                filename = _extract_header_param(header_line, "filename")
            elif header_lower.startswith("content-type:"):
                content_type_header = header_line.split(":", 1)[1].strip()

        if field_name is None:
            continue

        # If it has a filename, it's a file upload — wrap as UploadFile
        # Otherwise it's a regular form field — decode to string
        if filename is not None:
            value: Any = UploadFile(content=body_section, filename=filename, content_type=content_type_header)
        else:
            value = body_section.decode("utf-8")

        # Collect multiple values for same field name into a list
        if field_name in result:
            existing = result[field_name]
            if isinstance(existing, list):
                existing.append(value)
            else:
                result[field_name] = [existing, value]
        else:
            result[field_name] = value

    return result


def _extract_header_param(header_line: str, param_name: str) -> str | None:
    """Extract a parameter value from a header line (e.g., name="file" from Content-Disposition)."""
    search = f'{param_name}="'
    idx = header_line.find(search)
    if idx == -1:
        return None
    start = idx + len(search)
    end = header_line.find('"', start)
    if end == -1:
        return None
    return header_line[start:end]
