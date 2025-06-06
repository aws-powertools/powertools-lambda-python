from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.kafka_consumer.serialization.types import T


class OutputSerializerBase(ABC):
    """
    Abstract base class for output serializers.

    This class defines the interface for serializers that transform dictionary data
    into specific output formats or class instances.

    Methods
    -------
    serialize(data, output_class)
        Abstract method that must be implemented by subclasses to serialize data.

    Examples
    --------
    >>> class MyOutputSerializer(OutputSerializerBase):
    ...     def serialize(self, data: dict[str, Any], output_class=None):
    ...         if output_class:
    ...             # Convert dictionary to class instance
    ...             return output_class(**data)
    ...         return data  # Return as is if no output class provided
    """
    @abstractmethod
    def serialize(self, data: dict[str, Any], output_class: type[T] | None = None) -> T | dict[str, Any]:
        """
        Serialize dictionary data into a specific output format or class instance.

        This abstract method must be implemented by subclasses to provide
        specific serialization logic.

        Parameters
        ----------
        data : dict[str, Any]
            The dictionary data to serialize.
        output_class : type[T] or None, optional
            Optional class type to convert the dictionary into. If provided,
            the method should return an instance of this class.

        Returns
        -------
        T or dict[str, Any]
            An instance of output_class if provided, otherwise a processed dictionary.
            The generic type T represents the type of the output_class.
        """
        pass
