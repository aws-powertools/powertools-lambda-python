from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from aws_lambda_powertools.utilities.kafka.serialization.base import OutputSerializerBase
from aws_lambda_powertools.utilities.kafka.serialization.types import T

if TYPE_CHECKING:
    from collections.abc import Callable


class DataclassOutputSerializer(OutputSerializerBase):
    def serialize(self, data: dict[str, Any], output: type[T] | Callable | None = None) -> T | dict[str, Any]:
        return cast(T, output(**data))
