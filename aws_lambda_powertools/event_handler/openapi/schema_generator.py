"""
OpenAPI schema generation for individual routes.

Extracted from Route to keep route configuration and schema generation
as separate concerns. All functions here are internal.
"""

from __future__ import annotations

import copy
import warnings
from typing import TYPE_CHECKING, Any, Literal, cast

from aws_lambda_powertools.event_handler.openapi.types import (
    COMPONENT_REF_PREFIX,
    METHODS_WITH_BODY,
    OpenAPIResponse,
    OpenAPIResponseContentModel,
    OpenAPIResponseContentSchema,
    response_validation_error_response_definition,
    validation_error_definition,
    validation_error_response_definition,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from http import HTTPStatus

    from aws_lambda_powertools.event_handler.openapi.compat import (
        JsonSchemaValue,
        ModelField,
    )
    from aws_lambda_powertools.event_handler.openapi.params import Dependant, Param
    from aws_lambda_powertools.event_handler.openapi.types import TypeModelOrEnum

from aws_lambda_powertools.event_handler.openapi.constants import (
    DEFAULT_CONTENT_TYPE,
    DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
    DEFAULT_STATUS_CODE,
)


def generate_openapi_path(
    *,
    method: str,
    operation_id: str,
    summary: str | None,
    description: str | None,
    openapi_path: str,
    tags: list[str],
    deprecated: bool,
    security: list[dict[str, list[str]]] | None,
    openapi_extensions: dict[str, Any] | None,
    responses: dict[int, OpenAPIResponse] | None,
    response_description: str | None,
    body_field: ModelField | None,
    custom_response_validation_http_code: HTTPStatus | None,
    status_code: int = DEFAULT_STATUS_CODE,
    dependant: Dependant,
    operation_ids: set[str],
    model_name_map: dict[TypeModelOrEnum, str],
    field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
    enable_validation: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Generate the OpenAPI path spec and definitions for a single route.
    """
    from aws_lambda_powertools.event_handler.openapi.dependant import get_flat_params

    definitions: dict[str, Any] = {}

    # Build operation metadata
    operation = _build_operation_metadata(
        method=method,
        operation_id=operation_id,
        summary=summary,
        description=description,
        openapi_path=openapi_path,
        tags=tags,
        deprecated=deprecated,
        operation_ids=operation_ids,
        func_name=dependant.call.__name__ if dependant.call else "",
        func_file=getattr(dependant.call, "__globals__", {}).get("__file__") if dependant.call else None,
    )

    _apply_optional_fields(operation, security=security, openapi_extensions=openapi_extensions)

    # Build parameters
    all_route_params = get_flat_params(dependant)
    parameters = _build_operation_parameters(
        all_route_params=all_route_params,
        model_name_map=model_name_map,
        field_mapping=field_mapping,
    )

    if parameters:
        operation["parameters"] = _deduplicate_parameters(parameters)

    # Build request body
    _apply_request_body(
        operation,
        method=method,
        body_field=body_field,
        model_name_map=model_name_map,
        field_mapping=field_mapping,
    )

    # Build responses
    operation_responses, response_definitions = _build_responses(
        responses=responses,
        response_description=response_description,
        custom_response_validation_http_code=custom_response_validation_http_code,
        status_code=status_code,
        dependant=dependant,
        model_name_map=model_name_map,
        field_mapping=field_mapping,
        enable_validation=enable_validation,
    )
    definitions.update(response_definitions)

    operation["responses"] = operation_responses
    path = {method.lower(): operation}

    _add_validation_error_definitions(definitions)

    return path, definitions


def _build_operation_metadata(
    *,
    method: str,
    operation_id: str,
    summary: str | None,
    description: str | None,
    openapi_path: str,
    tags: list[str],
    deprecated: bool,
    operation_ids: set[str],
    func_name: str,
    func_file: str | None,
) -> dict[str, Any]:
    """Build the OpenAPI operation metadata (tags, summary, operationId, etc.)."""
    _warn_duplicate_operation_id(operation_id, operation_ids, func_name, func_file)
    operation_ids.add(operation_id)

    operation: dict[str, Any] = {
        "summary": summary or f"{method.upper()} {openapi_path}",
        "operationId": operation_id,
        "deprecated": deprecated or None,
    }

    if tags:
        operation["tags"] = tags
    if description:
        operation["description"] = description

    return operation


def _build_operation_parameters(
    *,
    all_route_params: Sequence[ModelField],
    model_name_map: dict[TypeModelOrEnum, str],
    field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
) -> list[dict[str, Any]]:
    """Build the list of OpenAPI operation parameters."""
    from aws_lambda_powertools.event_handler.openapi.params import Param

    parameters: list[dict[str, Any]] = []

    for param in all_route_params:
        field_info = cast(Param, param.field_info)
        if not field_info.include_in_schema:
            continue

        if _is_pydantic_model_param(field_info):
            parameters.extend(_expand_pydantic_model_parameters(field_info))
        else:
            parameters.append(_create_regular_parameter(param, model_name_map, field_mapping))

    return parameters


def _build_request_body(
    *,
    body_field: ModelField | None,
    model_name_map: dict[TypeModelOrEnum, str],
    field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
) -> dict[str, Any] | None:
    """Build the OpenAPI request body spec."""
    from aws_lambda_powertools.event_handler.openapi.compat import ModelField as ModelFieldClass
    from aws_lambda_powertools.event_handler.openapi.compat import get_schema_from_model_field
    from aws_lambda_powertools.event_handler.openapi.params import Body

    if not body_field:
        return None

    if not isinstance(body_field, ModelFieldClass):
        raise AssertionError(f"Expected ModelField, got {body_field}")

    body_schema = get_schema_from_model_field(
        field=body_field,
        model_name_map=model_name_map,
        field_mapping=field_mapping,
    )

    field_info = cast(Body, body_field.field_info)

    request_body_oai: dict[str, Any] = {}
    if body_field.required:
        request_body_oai["required"] = body_field.required
    if field_info.description:
        request_body_oai["description"] = field_info.description

    request_body_oai["content"] = {
        field_info.media_type: _build_media_content(body_schema, field_info.openapi_examples),
    }
    return request_body_oai


def _build_responses(
    *,
    responses: dict[int, OpenAPIResponse] | None,
    response_description: str | None,
    custom_response_validation_http_code: HTTPStatus | None,
    status_code: int = DEFAULT_STATUS_CODE,
    dependant: Dependant,
    model_name_map: dict[TypeModelOrEnum, str],
    field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
    enable_validation: bool,
) -> tuple[dict[int, OpenAPIResponse], dict[str, Any]]:
    """Build the OpenAPI response specs and any extra definitions."""
    definitions: dict[str, Any] = {}
    operation_responses: dict[int, OpenAPIResponse] = {}

    _add_validation_responses(operation_responses, enable_validation=enable_validation)
    _add_response_validation_error(
        operation_responses,
        definitions,
        custom_response_validation_http_code=custom_response_validation_http_code,
    )

    if responses:
        for resp_code in list(responses):
            operation_responses[resp_code] = _build_custom_response(
                response=copy.deepcopy(responses[resp_code]),
                dependant=dependant,
                model_name_map=model_name_map,
                field_mapping=field_mapping,
            )
    else:
        response_schema = _build_return_schema(
            param=dependant.return_param,
            model_name_map=model_name_map,
            field_mapping=field_mapping,
        )

        operation_responses[status_code] = {
            "description": response_description or DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
            "content": {DEFAULT_CONTENT_TYPE: response_schema},
        }

    return operation_responses, definitions


def _build_return_schema(
    *,
    param: ModelField | None,
    model_name_map: dict[TypeModelOrEnum, str],
    field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
) -> OpenAPIResponseContentSchema:
    """Build the response schema for a return parameter."""
    if param is None:
        return {}

    from aws_lambda_powertools.event_handler.openapi.compat import get_schema_from_model_field

    return_schema = get_schema_from_model_field(
        field=param,
        model_name_map=model_name_map,
        field_mapping=field_mapping,
    )

    return {"schema": return_schema}


def _is_pydantic_model_param(field_info: Param) -> bool:
    """Check if the field info represents a Pydantic model parameter."""
    from pydantic import BaseModel

    from aws_lambda_powertools.event_handler.openapi.compat import lenient_issubclass

    return lenient_issubclass(field_info.annotation, BaseModel)


def _expand_pydantic_model_parameters(field_info: Param) -> list[dict[str, Any]]:
    """Expand a Pydantic model into individual OpenAPI parameters."""
    from pydantic import BaseModel

    model_class = cast(type[BaseModel], field_info.annotation)
    parameters: list[dict[str, Any]] = []

    for field_name, field_def in model_class.model_fields.items():
        param_name = field_def.alias or field_name
        individual_param = _create_pydantic_field_parameter(
            param_name=param_name,
            field_def=field_def,
            param_location=field_info.in_.value,
        )
        parameters.append(individual_param)

    return parameters


def _create_pydantic_field_parameter(
    param_name: str,
    field_def: Any,
    param_location: str,
) -> dict[str, Any]:
    """Create an OpenAPI parameter from a Pydantic field definition."""
    individual_param: dict[str, Any] = {
        "name": param_name,
        "in": param_location,
        "required": field_def.is_required() if hasattr(field_def, "is_required") else field_def.default is ...,
        "schema": _get_basic_type_schema(field_def.annotation or type(None)),
    }

    if field_def.description:
        individual_param["description"] = field_def.description

    return individual_param


def _create_regular_parameter(
    param: ModelField,
    model_name_map: dict[TypeModelOrEnum, str],
    field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
) -> dict[str, Any]:
    """Create an OpenAPI parameter from a regular ModelField."""
    from aws_lambda_powertools.event_handler.openapi.compat import get_schema_from_model_field
    from aws_lambda_powertools.event_handler.openapi.params import Param

    field_info = cast(Param, param.field_info)
    param_schema = get_schema_from_model_field(
        field=param,
        model_name_map=model_name_map,
        field_mapping=field_mapping,
    )

    parameter: dict[str, Any] = {
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

    return parameter


def _get_basic_type_schema(param_type: type) -> dict[str, str]:
    """Get basic OpenAPI schema for simple types."""
    type_map: dict[type, str] = {bool: "boolean", int: "integer", float: "number"}
    try:
        for base_type, schema_type in type_map.items():
            if issubclass(param_type, base_type):
                return {"type": schema_type}
        return {"type": "string"}
    except TypeError:
        return {"type": "string"}


def _apply_optional_fields(
    operation: dict[str, Any],
    *,
    security: list[dict[str, list[str]]] | None,
    openapi_extensions: dict[str, Any] | None,
) -> None:
    """Apply optional security and extension fields to the operation."""
    if security:
        operation["security"] = security
    if openapi_extensions:
        operation.update(openapi_extensions)


def _apply_request_body(
    operation: dict[str, Any],
    *,
    method: str,
    body_field: ModelField | None,
    model_name_map: dict[TypeModelOrEnum, str],
    field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
) -> None:
    """Build and apply request body to operation if applicable."""
    if method.upper() not in METHODS_WITH_BODY:
        return

    request_body_oai = _build_request_body(
        body_field=body_field,
        model_name_map=model_name_map,
        field_mapping=field_mapping,
    )
    if request_body_oai:
        operation["requestBody"] = request_body_oai


def _add_validation_responses(
    operation_responses: dict[int, OpenAPIResponse],
    *,
    enable_validation: bool,
) -> None:
    """Add 422 validation error response if validation is enabled."""
    if not enable_validation:
        return

    operation_responses[422] = {
        "description": "Validation Error",
        "content": {
            DEFAULT_CONTENT_TYPE: {"schema": {"$ref": f"{COMPONENT_REF_PREFIX}HTTPValidationError"}},
        },
    }


def _add_response_validation_error(
    operation_responses: dict[int, OpenAPIResponse],
    definitions: dict[str, Any],
    *,
    custom_response_validation_http_code: HTTPStatus | None,
) -> None:
    """Add response validation error if a custom HTTP code is configured."""
    if not custom_response_validation_http_code:
        return

    http_code = custom_response_validation_http_code.value
    operation_responses[http_code] = {
        "description": "Response Validation Error",
        "content": {
            DEFAULT_CONTENT_TYPE: {"schema": {"$ref": f"{COMPONENT_REF_PREFIX}ResponseValidationError"}},
        },
    }
    definitions["ResponseValidationError"] = response_validation_error_response_definition


def _deduplicate_parameters(parameters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate parameters, giving priority to required ones."""
    all_parameters = {(param["in"], param["name"]): param for param in parameters}
    required_parameters = {(param["in"], param["name"]): param for param in parameters if param.get("required")}
    all_parameters.update(required_parameters)
    return list(all_parameters.values())


def _add_validation_error_definitions(definitions: dict[str, Any]) -> None:
    """Add standard validation error schema definitions if not already present."""
    if "ValidationError" not in definitions:
        definitions["ValidationError"] = validation_error_definition
        definitions["HTTPValidationError"] = validation_error_response_definition


def _warn_duplicate_operation_id(
    operation_id: str,
    operation_ids: set[str],
    func_name: str,
    func_file: str | None,
) -> None:
    """Warn if an operationId has already been used."""
    if operation_id not in operation_ids:
        return

    message = f"Duplicate Operation ID {operation_id} for function {func_name}"
    if func_file:
        message += f" in {func_file}"
    warnings.warn(message, stacklevel=1)


def _build_media_content(
    body_schema: dict[str, Any],
    openapi_examples: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build the media content dict for a request body."""
    content: dict[str, Any] = {"schema": body_schema}
    if openapi_examples:
        content["examples"] = openapi_examples
    return content


def _build_custom_response(
    *,
    response: OpenAPIResponse,
    dependant: Dependant,
    model_name_map: dict[TypeModelOrEnum, str],
    field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
) -> OpenAPIResponse:
    """Build a single custom response, resolving model references in content."""
    if "content" not in response:
        response["content"] = {
            DEFAULT_CONTENT_TYPE: _build_return_schema(
                param=dependant.return_param,
                model_name_map=model_name_map,
                field_mapping=field_mapping,
            ),
        }
        return response

    for content_type, payload in response["content"].items():
        response["content"][content_type] = _resolve_response_payload(
            payload=payload,
            dependant=dependant,
            model_name_map=model_name_map,
            field_mapping=field_mapping,
        )

    return response


def _resolve_response_payload(
    *,
    payload: OpenAPIResponseContentSchema | OpenAPIResponseContentModel,
    dependant: Dependant,
    model_name_map: dict[TypeModelOrEnum, str],
    field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
) -> OpenAPIResponseContentSchema:
    """Resolve a single response content payload, replacing model refs with schemas."""
    if "model" not in payload:
        return cast(OpenAPIResponseContentSchema, payload)

    model_payload_typed = cast(OpenAPIResponseContentModel, payload)
    return_field = next(
        filter(
            lambda model: model.type_ is model_payload_typed["model"],
            dependant.response_extra_models,
        ),
    )
    if not return_field:
        raise AssertionError("Model declared in custom responses was not found")

    model_payload = _build_return_schema(
        param=return_field,
        model_name_map=model_name_map,
        field_mapping=field_mapping,
    )

    new_payload: OpenAPIResponseContentSchema = {}
    for key, value in payload.items():
        if key != "model":
            new_payload[key] = value  # type: ignore[literal-required]
    new_payload.update(model_payload)
    return new_payload
