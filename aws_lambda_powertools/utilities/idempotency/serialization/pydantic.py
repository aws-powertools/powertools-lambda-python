from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyModelTypeError,
    IdempotencyNoSerializationModelError,
)
from aws_lambda_powertools.utilities.idempotency.serialization.base import (
    BaseIdempotencyModelSerializer,
    BaseIdempotencySerializer,
)
from aws_lambda_powertools.utilities.idempotency.serialization.functions import get_actual_type


class PydanticSerializer(BaseIdempotencyModelSerializer):
    """Pydantic serializer for idempotency models"""

    def __init__(self, model: type[BaseModel]):
        """
        Parameters
        ----------
        model: Model
            Pydantic model to be used for serialization
        """
        self.__model: type[BaseModel] = model

    def to_dict(self, data: BaseModel) -> dict:
        return data.model_dump()

    def from_dict(self, data: dict) -> BaseModel:
        return self.__model.model_validate(data)

    @classmethod
    def instantiate(cls, model_type: Any) -> BaseIdempotencySerializer:

        model_type = get_actual_type(model_type=model_type)

        if model_type is None:
            raise IdempotencyNoSerializationModelError("No serialization model was supplied")

        if not issubclass(model_type, BaseModel):
            raise IdempotencyModelTypeError("Model type is not inherited from pydantic BaseModel")

        return cls(model=model_type)
