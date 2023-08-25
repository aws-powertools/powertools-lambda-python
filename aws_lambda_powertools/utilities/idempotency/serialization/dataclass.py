from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Type

from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyModelTypeError,
    IdempotencyNoSerializationModelError,
)
from aws_lambda_powertools.utilities.idempotency.serialization.base import (
    BaseIdempotencyModelSerializer,
    BaseIdempotencySerializer,
)

DataClass = Any


class DataclassSerializer(BaseIdempotencyModelSerializer):
    def __init__(self, model: Type[DataClass]):
        """
        Parameters
        ----------
        model: Model
            A Pydantic model of the type to transform
        """
        self.__model: Type[DataClass] = model

    def to_dict(self, data: DataClass) -> Dict:
        return asdict(data)

    def from_dict(self, data: Dict) -> DataClass:
        return self.__model(**data)

    @classmethod
    def instantiate(cls, model_type: Any) -> BaseIdempotencySerializer:
        if model_type is None:
            raise IdempotencyNoSerializationModelError("No serialization model was supplied")

        if not is_dataclass(model_type):
            raise IdempotencyModelTypeError("Model type is not inherited of dataclass type")
        return cls(model=model_type)
