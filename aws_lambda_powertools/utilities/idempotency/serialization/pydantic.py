from typing import Dict, TypeVar

from pydantic import BaseModel

from aws_lambda_powertools.utilities.idempotency.serialization.base import BaseDictSerializer

Model = TypeVar("Model", bound=BaseModel)


class PydanticSerializer(BaseDictSerializer):
    def __init__(self, model: Model):
        self.__model: Model = model

    def to_dict(self, data: Model) -> Dict:
        if callable(getattr(data, "model_dump", None)):
            # Support for pydantic V2
            return data.model_dump()
        return data.dict()

    def from_dict(self, data: Dict) -> Model:
        if callable(getattr(self.__model, "model_validate", None)):
            # Support for pydantic V2
            return self.__model.model_validate(data)
        return self.__model.parse_obj(data)
