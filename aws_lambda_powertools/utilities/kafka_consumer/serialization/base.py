from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.kafka_consumer.serialization.types import T


class OutputSerializerBase(ABC):
    @abstractmethod
    def serialize(self, data: dict[str, Any], output_class: type[T] | None = None) -> T | dict[str, Any]:
        pass
