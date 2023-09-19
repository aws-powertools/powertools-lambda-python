from typing import Any, Callable, List, Optional, Tuple, Type, Union

from pydantic import BaseConfig
from pydantic.fields import FieldInfo, ModelField, Undefined, UndefinedType

from aws_lambda_powertools.event_handler.openapi.params import Dependant

CacheKey = Tuple[Optional[Callable[..., Any]], Tuple[str, ...]]


def get_flat_dependant(
    dependant: Dependant,
    *,
    skip_repeats: bool = False,
    visited: Optional[List[CacheKey]] = None,
) -> Dependant:
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
    flat_dependant = get_flat_dependant(dependant, skip_repeats=True)
    return (
        flat_dependant.path_params
        + flat_dependant.query_params
        + flat_dependant.header_params
        + flat_dependant.cookie_params
    )


def create_response_field(
    name: str,
    type_: Type[Any],
    default: Optional[Any] = Undefined,
    required: Union[bool, UndefinedType] = Undefined,
    model_config: Type[BaseConfig] = BaseConfig,
    alias: Optional[str] = None,
) -> ModelField:
    """
    Create a new response field.
    """
    field_info = FieldInfo()

    kwargs = {
        "name": name,
        "field_info": field_info,
        "type_": type_,
        "default": default,
        "required": required,
        "model_config": model_config,
        "alias": alias,
        "class_validators": {},
    }
    return ModelField(**kwargs)
