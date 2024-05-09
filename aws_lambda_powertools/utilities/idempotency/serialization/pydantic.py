from typing import Any, Dict, Type

from pydantic import BaseModel

from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyModelTypeError,
    IdempotencyNoSerializationModelError,
)
from aws_lambda_powertools.utilities.idempotency.serialization.base import (
    BaseIdempotencyModelSerializer,
    BaseIdempotencySerializer,
)


class PydanticSerializer(BaseIdempotencyModelSerializer):
    """Pydantic serializer for idempotency models"""

    def __init__(self, model: Type[BaseModel]):
        """
        Parameters
        ----------
        model: Model
            Pydantic model to be used for serialization
        """
        self.__model: Type[BaseModel] = model

    def to_dict(self, data: BaseModel) -> Dict:
        return data.model_dump()

    def from_dict(self, data: Dict) -> BaseModel:
        return self.__model.model_validate(data)

    @classmethod
    def instantiate(cls, model_type: Any) -> BaseIdempotencySerializer:
        if model_type is None:
            raise IdempotencyNoSerializationModelError("No serialization model was supplied")

        if not issubclass(model_type, BaseModel):
            raise IdempotencyModelTypeError("Model type is not inherited from pydantic BaseModel")

        return cls(model=model_type)
