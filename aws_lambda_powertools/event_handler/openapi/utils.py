from typing import Any, Callable, List, Optional

from pydantic.fields import ModelField

from aws_lambda_powertools.event_handler.openapi.params import Dependant

CacheKey = Optional[Callable[..., Any]]

"""
This file defines utility functions for working with OpenAPI/JSON Schema models.
"""


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
