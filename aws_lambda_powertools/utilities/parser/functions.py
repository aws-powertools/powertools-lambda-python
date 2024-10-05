from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from pydantic import TypeAdapter

from aws_lambda_powertools.shared.cache_dict import LRUDict

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser.types import T

CACHE_TYPE_ADAPTER = LRUDict(max_items=1024)

logger = logging.getLogger(__name__)


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


def _parse_and_validate_event(data: dict[str, Any] | Any, adapter: TypeAdapter):
    """
    Parse and validate the event data using the provided adapter.

    Params
    ------
    data: dict | Any
        The event data to be parsed and validated.
    adapter: TypeAdapter
        The adapter object used for validation.

    Returns:
        dict: The validated event data.

    Raises:
        ValidationError: If the data is invalid or cannot be parsed.
    """
    logger.debug("Parsing event against model")

    if isinstance(data, str):
        logger.debug("Parsing event as string")
        try:
            return adapter.validate_json(data)
        except NotImplementedError:
            # See: https://github.com/aws-powertools/powertools-lambda-python/issues/5303
            # See: https://github.com/pydantic/pydantic/issues/8890
            logger.debug(
                "Falling back to Python validation due to Pydantic implementation."
                "See issue: https://github.com/aws-powertools/powertools-lambda-python/issues/5303",
            )
            data = json.loads(data)

    return adapter.validate_python(data)
