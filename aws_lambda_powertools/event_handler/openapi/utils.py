from typing import TYPE_CHECKING, List, Optional

from aws_lambda_powertools.event_handler.openapi.types import CacheKey

if TYPE_CHECKING:
    from aws_lambda_powertools.event_handler.openapi.dependant import Dependant


def get_flat_dependant(
    dependant: "Dependant",
    *,
    skip_repeats: bool = False,
    visited: Optional[List[CacheKey]] = None,
) -> "Dependant":
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

    from aws_lambda_powertools.event_handler.openapi.dependant import Dependant

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
