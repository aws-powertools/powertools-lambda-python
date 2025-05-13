from __future__ import annotations

from typing import Any, Literal

try:
    from pydantic import BaseModel

    PydanticModelType = type[BaseModel] | BaseModel
except ImportError:
    PydanticModelType = Any  # Fallback Pydantic is not available


class SchemaConfig:
    """
    Configuration class for managing schema types and serialization for Kafka messages.

    This class holds the schema information and serialization configuration for both
    message keys and values in a Kafka messaging context.

    Parameters
    ----------
    value_schema_type : {'AVRO', 'PROTOBUF', 'JSON'}, default='JSON'
        Schema type for message values
    value_schema_str : str, optional
        Schema definition string for message values
        Required when value_schema_type is 'AVRO' or 'PROTOBUF'
    value_output_serializer : type[BaseModel] | BaseModel | type | Callable | None
        Custom serializer for message values. Can be:
        - Pydantic model class
        - Pydantic model instance
        - Python dataclass
        - Regular Python class
        - Custom serializer function
    key_schema_type : {'AVRO', 'PROTOBUF', 'JSON'}, default='JSON'
        Schema type for message keys
    key_schema_str : str, optional
        Schema definition string for message keys
        Required when key_schema_type is 'AVRO' or 'PROTOBUF'
    key_output_serializer : type[BaseModel] | BaseModel | type | Callable | None
        Custom serializer for message keys. Can be:
        - Pydantic model class
        - Pydantic model instance
        - Python dataclass
        - Regular Python class
        - Custom serializer function

    Raises
    ------
    ValueError
        If value_schema_type is 'AVRO' or 'PROTOBUF' and value_schema_str is not provided
        If key_schema_type is 'AVRO' or 'PROTOBUF' and key_schema_str is not provided
    """

    def __init__(
        self,
        value_schema_type: Literal["AVRO", "PROTOBUF", "JSON"] = "JSON",
        value_schema_str: str | None = None,
        value_output_serializer: Any | None = None,
        key_schema_type: Literal["AVRO", "PROTOBUF", "JSON"] = "JSON",
        key_schema_str: str | None = None,
        key_output_serializer: Any | None = None,
    ):
        # Validate schema requirements for value
        if value_schema_type in ["AVRO", "PROTOBUF"] and value_schema_str is None:
            raise ValueError(f"value_schema_str must be provided when value_schema_type is {value_schema_type}")

        # Validate schema requirements for key
        if key_schema_type in ["AVRO", "PROTOBUF"] and key_schema_str is None:
            raise ValueError(f"key_schema_str must be provided when key_schema_type is {key_schema_type}")

        self.value_schema_type = value_schema_type
        self.value_schema_str = value_schema_str
        self.value_output_serializer = value_output_serializer
        self.key_schema_type = key_schema_type
        self.key_schema_str = key_schema_str
        self.key_output_serializer = key_output_serializer
