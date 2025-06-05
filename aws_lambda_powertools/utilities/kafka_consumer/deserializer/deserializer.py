from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.kafka_consumer.deserializer.json import JsonDeserializer
from aws_lambda_powertools.utilities.kafka_consumer.deserializer.no_op import NoOpDeserializer

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.kafka_consumer.deserializer.base import DeserializerBase


def get_deserializer(schema_type: str | object, schema_value: Any) -> DeserializerBase:
    """
    Factory function to get the appropriate deserializer based on schema type.

    This function creates and returns a deserializer instance that corresponds to the
    specified schema type. It handles lazy imports for optional dependencies.

    Parameters
    ----------
    schema_type : str
        The type of schema to use for deserialization.
        Supported values are: "AVRO", "PROTOBUF", "JSON", or any other value for no-op.
    schema_value : Any
        The schema definition to use for deserialization. The format depends on the
        schema_type:
        - For "AVRO": A string containing the Avro schema definition
        - For "PROTOBUF": A object containing the Protobuf schema definition
        - For "JSON": Not used (can be None)
        - For other types: Not used (can be None)

    Returns
    -------
    DeserializerBase
        An instance of a deserializer that implements the DeserializerBase interface.

    Examples
    --------
    >>> # Get an Avro deserializer
    >>> avro_schema = '''
    ...     {
    ...       "type": "record",
    ...       "name": "User",
    ...       "fields": [
    ...         {"name": "name", "type": "string"},
    ...         {"name": "age", "type": "int"}
    ...       ]
    ...     }
    ... '''
    >>> deserializer = get_deserializer("AVRO", avro_schema)
    >>>
    >>> # Get a JSON deserializer
    >>> json_deserializer = get_deserializer("JSON", None)
    >>>
    >>> # Get a no-op deserializer for raw data
    >>> no_op_deserializer = get_deserializer("RAW", None)
    """
    if schema_type == "AVRO":
        # Import here to avoid dependency if not used
        from aws_lambda_powertools.utilities.kafka_consumer.deserializer.avro import AvroDeserializer

        return AvroDeserializer(schema_value)
    elif schema_type == "PROTOBUF":
        # Import here to avoid dependency if not used
        from aws_lambda_powertools.utilities.kafka_consumer.deserializer.protobuf import ProtobufDeserializer

        return ProtobufDeserializer(schema_value)
    elif schema_type == "JSON":
        return JsonDeserializer()

    return NoOpDeserializer()
