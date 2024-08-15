from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from aws_lambda_powertools.shared.cache_dict import LRUDict

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser.types import T

CACHE_TYPE_ADAPTER = LRUDict(max_items=1024)


def _retrieve_or_set_model_from_cache(model: type[T]) -> TypeAdapter:
    """
    Retrieves or sets a TypeAdapter instance from the cache for the given model.

    If the model is already present in the cache, the corresponding TypeAdapter
    instance is returned. Otherwise, a new TypeAdapter instance is created,
    stored in the cache, and returned.

    Parameters
    ----------
    model: type[T]
        The model type for which the TypeAdapter instance should be retrieved or set.

    Returns
    -------
    TypeAdapter
        The TypeAdapter instance for the given model,
        either retrieved from the cache or newly created and stored in the cache.
    """
    id_model = id(model)

    if id_model in CACHE_TYPE_ADAPTER:
        return CACHE_TYPE_ADAPTER[id_model]

    CACHE_TYPE_ADAPTER[id_model] = TypeAdapter(model)
    return CACHE_TYPE_ADAPTER[id_model]
