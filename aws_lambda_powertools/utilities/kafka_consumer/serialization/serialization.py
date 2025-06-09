from __future__ import annotations

from dataclasses import is_dataclass
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.kafka_consumer.serialization.custom_dict import CustomDictOutputSerializer
from aws_lambda_powertools.utilities.kafka_consumer.serialization.dataclass import DataclassOutputSerializer

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.kafka_consumer.serialization.types import T


def _get_output_serializer(output_class: type[T] | None = None) -> Any:
    """
    Returns the appropriate serializer for the given output class.
    Uses lazy imports to avoid unnecessary dependencies.
    """
    if output_class is None:
        # Return a pass-through serializer if no output class is specified
        return CustomDictOutputSerializer()

    # Check if it's a dataclass
    if is_dataclass(output_class):
        return DataclassOutputSerializer()

    if _is_pydantic_model(output_class):
        from aws_lambda_powertools.utilities.kafka_consumer.serialization.pydantic import PydanticOutputSerializer

        return PydanticOutputSerializer()

    # Default to custom serializer
    return CustomDictOutputSerializer()


def _is_pydantic_model(obj: Any) -> bool:
    if isinstance(obj, type):
        # Check for Pydantic model attributes without direct import
        has_model_fields = getattr(obj, "model_fields", None) is not None
        has_model_validate = callable(getattr(obj, "model_validate", None))
        return has_model_fields and has_model_validate
    return False


def serialize_to_output_type(data: object | dict[str, Any], output_class: type[T] | None = None) -> T | dict[str, Any]:
    """
    Helper function to directly serialize data to the specified output class
    """
    serializer = _get_output_serializer(output_class)
    return serializer.serialize(data, output_class)
