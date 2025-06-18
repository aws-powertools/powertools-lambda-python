from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.kafka.serialization.base import OutputSerializerBase

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.kafka.serialization.types import T


class CustomDictOutputSerializer(OutputSerializerBase):
    """
    Serializer that allows custom dict transformations.

    This serializer takes dictionary data and either returns it as-is or passes it
    through a custom transformation function provided as the output parameter.
    """

    def serialize(self, data: dict[str, Any], output: type[T] | Callable | None = None) -> T | dict[str, Any]:
        return data if output is None else output(data)  # type: ignore[call-arg]
