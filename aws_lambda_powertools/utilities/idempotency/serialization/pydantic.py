from typing import Dict, Type

from pydantic import BaseModel

from aws_lambda_powertools.utilities.idempotency.serialization.base import BaseDictSerializer

Model = BaseModel


class PydanticSerializer(BaseDictSerializer):
    def __init__(self, model: Type[Model]):
        """
        Parameters
        ----------
        model: Model
            A model of the type to transform
        """
        self.__model: Type[Model] = model

    def to_dict(self, data: Model) -> Dict:
        if callable(getattr(data, "model_dump", None)):
            # Support for pydantic V2
            return data.model_dump()  # type: ignore[unused-ignore,attr-defined]
        return data.dict()

    def from_dict(self, data: Dict) -> Model:
        if callable(getattr(self.__model, "model_validate", None)):
            # Support for pydantic V2
            return self.__model.model_validate(data)  # type: ignore[unused-ignore,attr-defined]
        return self.__model.parse_obj(data)
