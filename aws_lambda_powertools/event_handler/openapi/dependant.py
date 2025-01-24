from __future__ import annotations

import inspect
import re
from typing import TYPE_CHECKING, Any, Callable, ForwardRef, cast

from aws_lambda_powertools.event_handler.openapi.compat import (
    ModelField,
    create_body_model,
    evaluate_forwardref,
    is_scalar_field,
    is_scalar_sequence_field,
)
from aws_lambda_powertools.event_handler.openapi.params import (
    Body,
    Dependant,
    Header,
    Param,
    ParamTypes,
    Query,
    _File,
    _Form,
    analyze_param,
    create_response_field,
    get_flat_dependant,
)
from aws_lambda_powertools.event_handler.openapi.types import OpenAPIResponse, OpenAPIResponseContentModel

if TYPE_CHECKING:
    from pydantic import BaseModel

"""
This turns the opaque function signature into typed, validated models.

It relies on Pydantic's typing and validation to achieve this in a declarative way.
This enables traits like autocompletion, validation, and declarative structure vs imperative parsing.

This code parses an OpenAPI operation handler function signature into Pydantic models. It uses inspect to get the
signature and regex to parse path parameters. Each parameter is analyzed to extract its type annotation and generate
a corresponding Pydantic field, which are added to a Dependant model. Return values are handled similarly.

This modeling allows for type checking, automatic parameter name/location/type extraction, and input validation -
turning the opaque signature into validated models. It relies on Pydantic's typing and validation for a declarative
approach over imperative parsing, enabling autocompletion, validation and structure.
"""


def add_param_to_fields(
    *,
    field: ModelField,
    dependant: Dependant,
) -> None:
    """
    Adds a parameter to the list of parameters in the dependant model.

    Parameters
    ----------
    field: ModelField
        The field to add
    dependant: Dependant
        The dependant model to add the field to

    """
    field_info = cast(Param, field.field_info)

    # Dictionary to map ParamTypes to their corresponding lists in dependant
    param_type_map = {
        ParamTypes.path: dependant.path_params,
        ParamTypes.query: dependant.query_params,
        ParamTypes.header: dependant.header_params,
        ParamTypes.cookie: dependant.cookie_params,
    }

    # Check if field_info.in_ is a valid key in param_type_map and append the field to the corresponding list
    # or raise an exception if it's not a valid key.
    if field_info.in_ in param_type_map:
        param_type_map[field_info.in_].append(field)
    else:
        raise AssertionError(f"Unsupported param type: {field_info.in_}")


def get_typed_annotation(annotation: Any, globalns: dict[str, Any]) -> Any:
    """
    Evaluates a type annotation, which can be a string or a ForwardRef.
    """
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)
        annotation = evaluate_forwardref(annotation, globalns, globalns)
    return annotation


def get_typed_signature(call: Callable[..., Any]) -> inspect.Signature:
    """
    Returns a typed signature for a callable, resolving forward references.

    Parameters
    ----------
    call: Callable[..., Any]
        The callable to get the signature for

    Returns
    -------
    inspect.Signature
        The typed signature
    """
    signature = inspect.signature(call)

    # Gets the global namespace for the call. This is used to resolve forward references.
    globalns = getattr(call, "__globals__", {})

    typed_params = [
        inspect.Parameter(
            name=param.name,
            kind=param.kind,
            default=param.default,
            annotation=get_typed_annotation(param.annotation, globalns),
        )
        for param in signature.parameters.values()
    ]

    # If the return annotation is not empty, add it to the signature.
    if signature.return_annotation is not inspect.Signature.empty:
        return_param = inspect.Parameter(
            name="Return",
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=None,
            annotation=get_typed_annotation(signature.return_annotation, globalns),
        )
        return inspect.Signature(typed_params, return_annotation=return_param.annotation)
    else:
        return inspect.Signature(typed_params)


def get_path_param_names(path: str) -> set[str]:
    """
    Returns the path parameter names from a path template. Those are the strings between { and }.

    Parameters
    ----------
    path: str
        The path template

    Returns
    -------
    set[str]
        The path parameter names

    """
    return set(re.findall("{(.*?)}", path))


def get_dependant(
    *,
    path: str,
    call: Callable[..., Any],
    name: str | None = None,
    responses: dict[int, OpenAPIResponse] | None = None,
) -> Dependant:
    """
    Returns a dependant model for a handler function. A dependant model is a model that contains
    the parameters and return value of a handler function.

    Parameters
    ----------
    path: str
        The path template
    call: Callable[..., Any]
        The handler function
    name: str, optional
        The name of the handler function
    responses: list[dict[int, OpenAPIResponse]], optional
        The list of extra responses for the handler function

    Returns
    -------
    Dependant
        The dependant model for the handler function
    """
    path_param_names = get_path_param_names(path)
    endpoint_signature = get_typed_signature(call)
    signature_params = endpoint_signature.parameters

    dependant = Dependant(
        call=call,
        name=name,
        path=path,
    )

    # Add each parameter to the dependant model
    for param_name, param in signature_params.items():
        # If the parameter is a path parameter, we need to set the in_ field to "path".
        is_path_param = param_name in path_param_names

        # Analyze the parameter to get the Pydantic field.
        param_field = analyze_param(
            param_name=param_name,
            annotation=param.annotation,
            value=param.default,
            is_path_param=is_path_param,
            is_response_param=False,
        )
        if param_field is None:
            raise AssertionError(f"Parameter field is None for param: {param_name}")

        if is_body_param(param_field=param_field, is_path_param=is_path_param):
            dependant.body_params.append(param_field)
        else:
            add_param_to_fields(field=param_field, dependant=dependant)

    _add_return_annotation(dependant, endpoint_signature)
    _add_extra_responses(dependant, responses)

    return dependant


def _add_extra_responses(dependant: Dependant, responses: dict[int, OpenAPIResponse] | None):
    # Also add the optional extra responses to the dependant model.
    if not responses:
        return

    for response in responses.values():
        for schema in response.get("content", {}).values():
            if "model" in schema:
                response_field = analyze_param(
                    param_name="return",
                    annotation=cast(OpenAPIResponseContentModel, schema)["model"],
                    value=None,
                    is_path_param=False,
                    is_response_param=True,
                )
                if response_field is None:
                    raise AssertionError("Response field is None for response model")

                dependant.response_extra_models.append(response_field)


def _add_return_annotation(dependant: Dependant, endpoint_signature: inspect.Signature):
    # If the return annotation is not empty, add it to the dependant model.
    return_annotation = endpoint_signature.return_annotation
    if return_annotation is not inspect.Signature.empty:
        param_field = analyze_param(
            param_name="return",
            annotation=return_annotation,
            value=None,
            is_path_param=False,
            is_response_param=True,
        )
        if param_field is None:
            raise AssertionError("Param field is None for return annotation")

        dependant.return_param = param_field


def is_body_param(*, param_field: ModelField, is_path_param: bool) -> bool:
    """
    Returns whether a parameter is a request body parameter, by checking if it is a scalar field or a body field.

    Parameters
    ----------
    param_field: ModelField
        The parameter field
    is_path_param: bool
        Whether the parameter is a path parameter

    Returns
    -------
    bool
        Whether the parameter is a request body parameter
    """
    if is_path_param:
        if not is_scalar_field(field=param_field):
            raise AssertionError("Path params must be of one of the supported types")
        return False
    elif is_scalar_field(field=param_field):
        return False
    elif isinstance(param_field.field_info, (Query, Header)) and is_scalar_sequence_field(param_field):
        return False
    else:
        if not isinstance(param_field.field_info, Body):
            raise AssertionError(f"Param: {param_field.name} can only be a request body, use Body()")
        return True


def get_flat_params(dependant: Dependant) -> list[ModelField]:
    """
    Get a list of all the parameters from a Dependant object.

    Parameters
    ----------
    dependant : Dependant
        The Dependant object containing the parameters.

    Returns
    -------
    list[ModelField]
        A list of ModelField objects containing the flat parameters from the Dependant object.

    """
    flat_dependant = get_flat_dependant(dependant)
    return (
        flat_dependant.path_params
        + flat_dependant.query_params
        + flat_dependant.header_params
        + flat_dependant.cookie_params
    )


def get_body_field(*, dependant: Dependant, name: str) -> ModelField | None:
    """
    Get the Body field for a given Dependant object.
    """

    flat_dependant = get_flat_dependant(dependant)
    if not flat_dependant.body_params:
        return None

    first_param = flat_dependant.body_params[0]
    field_info = first_param.field_info

    # Handle the case where there is only one body parameter and it is embedded
    embed = getattr(field_info, "embed", None)
    body_param_names_set = {param.name for param in flat_dependant.body_params}
    if len(body_param_names_set) == 1 and not embed:
        return first_param

    # If one field requires to embed, all have to be embedded
    for param in flat_dependant.body_params:
        setattr(param.field_info, "embed", True)  # noqa: B010

    # Generate a custom body model for this endpoint
    model_name = "Body_" + name
    body_model = create_body_model(fields=flat_dependant.body_params, model_name=model_name)

    required = any(True for f in flat_dependant.body_params if f.required)

    body_field_info, body_field_info_kwargs = get_body_field_info(
        body_model=body_model,
        flat_dependant=flat_dependant,
        required=required,
    )

    final_field = create_response_field(
        name="body",
        type_=body_model,
        required=required,
        alias="body",
        field_info=body_field_info(**body_field_info_kwargs),
    )
    return final_field


def get_body_field_info(
    *,
    body_model: type[BaseModel],
    flat_dependant: Dependant,
    required: bool,
) -> tuple[type[Body], dict[str, Any]]:
    """
    Get the Body field info and kwargs for a given body model.
    """

    body_field_info_kwargs: dict[str, Any] = {"annotation": body_model, "alias": "body"}

    if not required:
        body_field_info_kwargs["default"] = None

    if any(isinstance(f.field_info, _File) for f in flat_dependant.body_params):
        # MAINTENANCE: body_field_info: type[Body] = _File
        raise NotImplementedError("_File fields are not supported in request bodies")
    elif any(isinstance(f.field_info, _Form) for f in flat_dependant.body_params):
        # MAINTENANCE: body_field_info: type[Body] = _Form
        raise NotImplementedError("_Form fields are not supported in request bodies")
    else:
        body_field_info = Body

        body_param_media_types = [
            f.field_info.media_type for f in flat_dependant.body_params if isinstance(f.field_info, Body)
        ]
        if len(set(body_param_media_types)) == 1:
            body_field_info_kwargs["media_type"] = body_param_media_types[0]

    return body_field_info, body_field_info_kwargs
