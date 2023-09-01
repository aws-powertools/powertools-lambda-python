"""
Serialization for supporting idempotency
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseIdempotencySerializer(ABC):
    """
    Abstract Base Class for Idempotency serialization layer, supporting dict operations.
    """

    @abstractmethod
    def to_dict(self, data: Any) -> Dict:
        raise NotImplementedError("Implementation of to_dict is required")

    @abstractmethod
    def from_dict(self, data: Dict) -> Any:
        raise NotImplementedError("Implementation of from_dict is required")


class BaseIdempotencyModelSerializer(BaseIdempotencySerializer):
    """
    Abstract Base Class for Idempotency serialization layer, for using a model as data object representation.
    """

    @classmethod
    @abstractmethod
    def instantiate(cls, model_type: Any) -> BaseIdempotencySerializer:
        """
        Creates an instance of a serializer based on a provided model type.
        In case the model_type is unknown, None will be sent as `model_type`.
        It's on the implementer to verify that:
        - None is handled correctly
        - A model type not matching the expected types is handled

        Parameters
        ----------
        model_type: Any
            The model type to instantiate the class for

        Returns
        -------
        BaseIdempotencySerializer
            Instance of the serializer class
        """
        pass
