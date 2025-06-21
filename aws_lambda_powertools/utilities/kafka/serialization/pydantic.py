from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import TypeAdapter

from aws_lambda_powertools.utilities.kafka.serialization.base import OutputSerializerBase

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.kafka.serialization.types import T

logger = logging.getLogger(__name__)


class PydanticOutputSerializer(OutputSerializerBase):
    """
    Serializer that converts dictionary data into Pydantic model instances.

    This serializer takes dictionary data and validates/converts it into an instance
    of the specified Pydantic model type using Pydantic's TypeAdapter.
    """

    def serialize(self, data: dict[str, Any], output: type[T] | Callable | None = None) -> T | dict[str, Any]:
        logger.debug("Serializing output data with PydanticOutputSerializer")
        # Use TypeAdapter for better support of Union types and other complex types
        adapter: TypeAdapter = TypeAdapter(output)
        return adapter.validate_python(data)
