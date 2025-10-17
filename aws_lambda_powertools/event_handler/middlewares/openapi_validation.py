from __future__ import annotations

import dataclasses
import json
import logging
import re
from typing import TYPE_CHECKING, Any, Callable, Mapping, MutableMapping, Sequence, Union, cast
from urllib.parse import parse_qs

from pydantic import BaseModel

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
from aws_lambda_powertools.event_handler.openapi.exceptions import RequestValidationError, ResponseValidationError
from aws_lambda_powertools.event_handler.openapi.params import Param, UploadFile

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
MULTIPART_FORM_CONTENT_TYPE = "multipart/form-data"


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

        # Handle multipart form data
        elif content_type.startswith(MULTIPART_FORM_CONTENT_TYPE):
            return self._parse_multipart_data(app, content_type)

        else:
            raise NotImplementedError(f"Content type '{content_type}' is not supported")

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
        """Parse multipart/form-data."""
        try:
            decoded_bytes = self._decode_request_body(app)
            boundary_bytes = self._extract_boundary_bytes(content_type)
            return self._parse_multipart_sections(decoded_bytes, boundary_bytes)

        except Exception as e:
            raise RequestValidationError(
                [
                    {
                        "type": "multipart_invalid",
                        "loc": ("body",),
                        "msg": "Invalid multipart form data",
                        "input": {},
                        "ctx": {"error": str(e)},
                    },
                ],
            ) from e

    def _decode_request_body(self, app: EventHandlerInstance) -> bytes:
        """Decode the request body, handling base64 encoding if necessary."""
        import base64

        body = app.current_event.body or ""

        if app.current_event.is_base64_encoded:
            try:
                return base64.b64decode(body)
            except Exception:
                # If decoding fails, use body as-is
                return body.encode("utf-8") if isinstance(body, str) else body
        else:
            return body.encode("utf-8") if isinstance(body, str) else body

    def _extract_boundary_bytes(self, content_type: str) -> bytes:
        """Extract and return the boundary bytes from the content type header."""
        boundary_match = re.search(r"boundary=([^;,\s]+)", content_type)

        if not boundary_match:
            # Handle WebKit browsers that may use different boundary formats
            webkit_match = re.search(r"WebKitFormBoundary([a-zA-Z0-9]+)", content_type)
            if webkit_match:
                boundary = "WebKitFormBoundary" + webkit_match.group(1)
            else:
                raise ValueError("No boundary found in multipart content-type")
        else:
            boundary = boundary_match.group(1).strip('"')

        return ("--" + boundary).encode("utf-8")

    def _parse_multipart_sections(self, decoded_bytes: bytes, boundary_bytes: bytes) -> dict[str, Any]:
        """Parse individual multipart sections from the decoded body."""
        parsed_data: dict[str, Any] = {}

        if not decoded_bytes:
            return parsed_data

        sections = decoded_bytes.split(boundary_bytes)

        for section in sections[1:-1]:  # Skip first empty and last closing parts
            if not section.strip():
                continue

            field_name, content = self._parse_multipart_section(section)
            if field_name:
                parsed_data[field_name] = content

        return parsed_data

    def _parse_multipart_section(self, section: bytes) -> tuple[str | None, bytes | str | UploadFile]:
        """Parse a single multipart section to extract field name and content."""
        headers_part, content = self._split_section_headers_and_content(section)

        if headers_part is None:
            return None, b""

        # Extract field name from Content-Disposition header
        name_match = re.search(r'name="([^"]+)"', headers_part)
        if not name_match:
            return None, b""

        field_name = name_match.group(1)

        # Check if it's a file field and process accordingly
        if "filename=" in headers_part:
            # It's a file - extract metadata and create UploadFile
            filename_match = re.search(r'filename="([^"]*)"', headers_part)
            filename = filename_match.group(1) if filename_match else None

            # Extract Content-Type if present
            content_type_match = re.search(r"Content-Type:\s*([^\r\n]+)", headers_part, re.IGNORECASE)
            content_type = content_type_match.group(1).strip() if content_type_match else None

            # Parse all headers from the section
            headers = {}
            for line_raw in headers_part.split("\n"):
                line = line_raw.strip()
                if ":" in line and not line.startswith("Content-Disposition"):
                    key, value = line.split(":", 1)
                    headers[key.strip()] = value.strip()

            # Create UploadFile instance with metadata
            upload_file = UploadFile(
                file=content,
                filename=filename,
                content_type=content_type,
                headers=headers,
            )
            return field_name, upload_file
        else:
            # It's a regular form field - decode as string
            return field_name, self._decode_form_field_content(content)

    def _split_section_headers_and_content(self, section: bytes) -> tuple[str | None, bytes]:
        """Split a multipart section into headers and content parts."""
        header_end = section.find(b"\r\n\r\n")
        if header_end == -1:
            header_end = section.find(b"\n\n")
            if header_end == -1:
                return None, b""
            content = section[header_end + 2 :].strip()
        else:
            content = section[header_end + 4 :].strip()

        headers_part = section[:header_end].decode("utf-8", errors="ignore")
        return headers_part, content

    def _decode_form_field_content(self, content: bytes) -> str | bytes:
        """Decode form field content as string, falling back to bytes if decoding fails."""
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            # If can't decode as text, keep as bytes
            return content


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
        # Process the response body if it exists
        if response.body and response.is_json():
            response.body = self._serialize_response(
                field=route.dependant.return_param,
                response_content=response.body,
                has_route_custom_response_validation=route.custom_response_validation_http_code is not None,
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
        has_route_custom_response_validation: bool = False,
    ) -> Any:
        """
        Serialize the response content according to the field type.
        """
        if field:
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


def _get_field_location(field: ModelField, field_alias_omitted: bool) -> tuple[str, ...]:
    """Get the location tuple for a field based on whether alias is omitted."""
    if field_alias_omitted:
        return ("body",)
    return ("body", field.alias)


def _get_field_value(received_body: dict[str, Any] | None, field: ModelField) -> Any | None:
    """Extract field value from received body, returning None if not found or on error."""
    if received_body is None:
        return None

    try:
        return received_body.get(field.alias)
    except AttributeError:
        return None


def _resolve_field_type(field_type: type) -> type:
    """Resolve the actual field type, handling Union types by returning the first non-None type."""
    from typing import get_args, get_origin

    if get_origin(field_type) is Union:
        union_args = get_args(field_type)
        non_none_types = [arg for arg in union_args if arg is not type(None)]
        if non_none_types:
            return non_none_types[0]
    return field_type


def _convert_value_type(value: Any, field_type: type) -> Any:
    """Convert value between UploadFile and bytes for type compatibility."""
    if isinstance(value, UploadFile) and field_type is bytes:
        # Convert UploadFile to bytes for backward compatibility
        return value.file
    elif isinstance(value, bytes) and field_type == UploadFile:
        # Convert bytes to UploadFile if that's what's expected
        return UploadFile(file=value)
    return value


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


def _normalize_field_value(value: Any, field_info: FieldInfo) -> Any:
    """Normalize field value, converting lists to single values for non-sequence fields."""
    # Convert UploadFile to bytes if the expected type is bytes
    if isinstance(value, UploadFile):
        # Check if the annotation is bytes
        annotation = field_info.annotation
        # Handle Annotated types by unwrapping
        if hasattr(annotation, "__origin__"):
            from typing import get_args

            args = get_args(annotation)
            if args:
                annotation = args[0]

        if annotation is bytes:
            return value.file

    if field_annotation_is_sequence(field_info.annotation):
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
