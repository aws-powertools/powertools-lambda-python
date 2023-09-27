import inspect
import re
from typing import Any, Callable, Dict, ForwardRef, List, Optional, Set, cast

from aws_lambda_powertools.event_handler.openapi.compat import ModelField, evaluate_forwardref
from aws_lambda_powertools.event_handler.openapi.params import Dependant, Param, ParamTypes, analyze_param
from aws_lambda_powertools.event_handler.openapi.types import CacheKey

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
    if field_info.in_ == ParamTypes.path:
        dependant.path_params.append(field)
    elif field_info.in_ == ParamTypes.query:
        dependant.query_params.append(field)
    elif field_info.in_ == ParamTypes.header:
        dependant.header_params.append(field)
    else:
        if field_info.in_ != ParamTypes.cookie:
            raise AssertionError(f"Unsupported param type: {field_info.in_}")
        dependant.cookie_params.append(field)


def get_typed_annotation(annotation: Any, globalns: Dict[str, Any]) -> Any:
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
    globalns = getattr(call, "__global__", {})

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


def get_path_param_names(path: str) -> Set[str]:
    """
    Returns the path parameter names from a path template. Those are the strings between < and >.

    Parameters
    ----------
    path: str
        The path template

    Returns
    -------
    Set[str]
        The path parameter names

    """
    return set(re.findall("<(.*?)>", path))


def get_dependant(
    *,
    path: str,
    call: Callable[..., Any],
    name: Optional[str] = None,
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

    for param_name, param in signature_params.items():
        # If the parameter is a path parameter, we need to set the in_ field to "path".
        is_path_param = param_name in path_param_names

        # Analyze the parameter to get the Pydantic field.
        _, param_field = analyze_param(
            param_name=param_name,
            annotation=param.annotation,
            value=param.default,
            is_path_param=is_path_param,
        )
        if param_field is None:
            raise AssertionError(f"Param field is None for param: {param_name}")

        add_param_to_fields(field=param_field, dependant=dependant)

    # If the return annotation is not empty, add it to the dependant model.
    return_annotation = endpoint_signature.return_annotation
    if return_annotation is not inspect.Signature.empty:
        _, param_field = analyze_param(
            param_name="Return",
            annotation=return_annotation,
            value=None,
            is_path_param=False,
        )
        if param_field is None:
            raise AssertionError("Param field is None for return annotation")

        dependant.return_param = param_field

    return dependant


def get_flat_dependant(
    dependant: Dependant,
    *,
    skip_repeats: bool = False,
    visited: Optional[List[CacheKey]] = None,
) -> Dependant:
    """
    Flatten a recursive Dependant model structure.

    This function recursively concatenates the parameter fields of a Dependant model and its dependencies into a flat
    Dependant structure. This is useful for scenarios like parameter validation where the nested structure is not
    relevant.

    Parameters
    ----------
    dependant: Dependant
        The dependant model to flatten
    skip_repeats: bool
        If True, child Dependents already visited will be skipped to avoid duplicates
    visited: List[CacheKey], optional
        Keeps track of visited Dependents to avoid infinite recursion. Defaults to empty list.

    Returns
    -------
    Dependant
        The flattened Dependant model
    """
    if visited is None:
        visited = []
    visited.append(dependant.cache_key)

    flat_dependant = Dependant(
        path_params=dependant.path_params.copy(),
        query_params=dependant.query_params.copy(),
        header_params=dependant.header_params.copy(),
        cookie_params=dependant.cookie_params.copy(),
        body_params=dependant.body_params.copy(),
        path=dependant.path,
    )
    for sub_dependant in dependant.dependencies:
        if skip_repeats and sub_dependant.cache_key in visited:
            continue

        flat_sub = get_flat_dependant(sub_dependant, skip_repeats=skip_repeats, visited=visited)

        flat_dependant.path_params.extend(flat_sub.path_params)
        flat_dependant.query_params.extend(flat_sub.query_params)
        flat_dependant.header_params.extend(flat_sub.header_params)
        flat_dependant.cookie_params.extend(flat_sub.cookie_params)
        flat_dependant.body_params.extend(flat_sub.body_params)

    return flat_dependant


def get_flat_params(dependant: Dependant) -> List[ModelField]:
    """
    Get a list of all the parameters from a Dependant object.

    Parameters
    ----------
    dependant : Dependant
        The Dependant object containing the parameters.

    Returns
    -------
    List[ModelField]
        A list of ModelField objects containing the flat parameters from the Dependant object.

    """
    flat_dependant = get_flat_dependant(dependant, skip_repeats=True)
    return (
        flat_dependant.path_params
        + flat_dependant.query_params
        + flat_dependant.header_params
        + flat_dependant.cookie_params
    )
