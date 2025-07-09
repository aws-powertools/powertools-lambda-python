from __future__ import annotations

import logging
from dataclasses import is_dataclass
from typing import TYPE_CHECKING, Any, cast

from aws_lambda_powertools.utilities.kafka.serialization.base import OutputSerializerBase
from aws_lambda_powertools.utilities.kafka.serialization.types import T

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class DataclassOutputSerializer(OutputSerializerBase):
    """
    Serializer that converts dictionary data into dataclass instances.

    This serializer takes dictionary data and converts it into an instance of the specified
    dataclass type.
    """

    def serialize(self, data: dict[str, Any], output: type[T] | Callable | None = None) -> T | dict[str, Any]:
        if not is_dataclass(output):  # pragma: no cover
            raise ValueError("Output class must be a dataclass")

        logger.debug("Serializing output data with DataclassOutputSerializer")

        return cast(T, output(**data))
