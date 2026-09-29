from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from aws_lambda_powertools.utilities.kafka.serialization.base import OutputSerializerBase

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.kafka.serialization.types import T

logger = logging.getLogger(__name__)


class CustomDictOutputSerializer(OutputSerializerBase):
    """
    Serializer that allows custom dict transformations.

    This serializer takes dictionary data and either returns it as-is or passes it
    through a custom transformation function provided as the output parameter.
    """

    def serialize(self, data: dict[str, Any], output: type[T] | Callable | None = None) -> T | dict[str, Any]:
        logger.debug("Serializing output data with CustomDictOutputSerializer")
        if output is None:
            return data
        return cast("Callable[[dict[str, Any]], T]", output)(data)
