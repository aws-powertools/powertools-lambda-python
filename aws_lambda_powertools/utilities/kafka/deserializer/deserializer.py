from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.kafka.deserializer.default import DefaultDeserializer
from aws_lambda_powertools.utilities.kafka.deserializer.json import JsonDeserializer

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.kafka.deserializer.base import DeserializerBase

# Cache for deserializers
_deserializer_cache: dict[str, DeserializerBase] = {}


def _get_cache_key(schema_type: str | object, schema_value: Any, field_metadata: dict[str, Any]) -> str:
    schema_metadata = None

    if field_metadata:
        schema_metadata = field_metadata.get("schemaId")

    if schema_value is None:
        schema_hash = f"{str(schema_type)}_{schema_metadata}"

    if isinstance(schema_value, str):
        hashable_value = f"{schema_value}_{schema_metadata}"
        # For string schemas like Avro, hash the content
        schema_hash = hashlib.md5(hashable_value.encode("utf-8"), usedforsecurity=False).hexdigest()
    else:
        # For objects like Protobuf, use the object id
        schema_hash = f"{str(id(schema_value))}_{schema_metadata}"

    return f"{schema_type}_{schema_hash}"


def get_deserializer(schema_type: str | object, schema_value: Any, field_metadata: Any) -> DeserializerBase:
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

    # Generate a cache key based on schema type and value
    cache_key = _get_cache_key(schema_type, schema_value, field_metadata)

    # Check if we already have this deserializer in cache
    if cache_key in _deserializer_cache:
        return _deserializer_cache[cache_key]

    deserializer: DeserializerBase

    if schema_type == "AVRO":
        # Import here to avoid dependency if not used
        from aws_lambda_powertools.utilities.kafka.deserializer.avro import AvroDeserializer

        deserializer = AvroDeserializer(schema_str=schema_value, field_metadata=field_metadata)
    elif schema_type == "PROTOBUF":
        # Import here to avoid dependency if not used
        from aws_lambda_powertools.utilities.kafka.deserializer.protobuf import ProtobufDeserializer

        deserializer = ProtobufDeserializer(message_class=schema_value, field_metadata=field_metadata)
    elif schema_type == "JSON":
        deserializer = JsonDeserializer(field_metadata=field_metadata)

    else:
        # Default to no-op deserializer
        deserializer = DefaultDeserializer()

    # Store in cache for future use
    _deserializer_cache[cache_key] = deserializer

    # Default to default deserializer that is base64 decode + bytes decoded
    return deserializer
