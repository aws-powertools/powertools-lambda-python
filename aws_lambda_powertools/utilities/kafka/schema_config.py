from __future__ import annotations

from typing import Any, Literal

from aws_lambda_powertools.utilities.kafka.exceptions import KafkaConsumerMissingSchemaError


class SchemaConfig:
    """
    Configuration for schema management in Kafka consumers.

    This class handles schema configuration for both keys and values in Kafka records,
    supporting AVRO, PROTOBUF, and JSON schema types.

    Parameters
    ----------
    value_schema_type : {'AVRO', 'PROTOBUF', 'JSON', None}, default=None
        Schema type for message values.
    value_schema : str, optional
        Schema definition for message values. Required when value_schema_type is 'AVRO' or 'PROTOBUF'.
    value_output_serializer : Any, optional
        Custom output serializer for message values. Supports Pydantic classes, Dataclasses and Custom Class
    value_schema_id_prefix_length : int, default=0
        Number of leading bytes to skip on the value payload before Avro deserialization. Use this
        when the payload was produced by a schema-registry-aware serializer (e.g. Confluent's
        5-byte magic byte + schema ID prefix) but you are supplying the Avro schema offline rather
        than relying on the ESM Schema Registry integration. Only applied for AVRO values.
    key_schema_type : {'AVRO', 'PROTOBUF', 'JSON', None}, default=None
        Schema type for message keys.
    key_schema : str, optional
        Schema definition for message keys. Required when key_schema_type is 'AVRO' or 'PROTOBUF'.
    key_output_serializer : Any, optional
        Custom serializer for message keys. Supports Pydantic classes, Dataclasses and Custom Class
    key_schema_id_prefix_length : int, default=0
        Same as ``value_schema_id_prefix_length`` but for the record key.

    Raises
    ------
    KafkaConsumerMissingSchemaError
        When schema_type is set to 'AVRO' or 'PROTOBUF' but the corresponding schema
        definition is not provided.

    Examples
    --------
    >>> # Configure with AVRO schema for values
    >>> avro_schema = '''
    ... {
    ...   "type": "record",
    ...   "name": "User",
    ...   "fields": [
    ...     {"name": "name", "type": "string"},
    ...     {"name": "age", "type": "int"}
    ...   ]
    ... }
    ... '''
    >>> config = SchemaConfig(value_schema_type="AVRO", value_schema=avro_schema)

    >>> # Configure with JSON schema for both keys and values
    >>> config = SchemaConfig(
    ...     value_schema_type="JSON",
    ...     key_schema_type="JSON"
    ... )
    """

    def __init__(
        self,
        value_schema_type: Literal["AVRO", "PROTOBUF", "JSON"] | None = None,
        value_schema: str | None = None,
        value_output_serializer: Any | None = None,
        value_schema_id_prefix_length: int = 0,
        key_schema_type: Literal["AVRO", "PROTOBUF", "JSON"] | None = None,
        key_schema: str | None = None,
        key_output_serializer: Any | None = None,
        key_schema_id_prefix_length: int = 0,
    ):
        # Validate schema requirements
        self._validate_schema_requirements(value_schema_type, value_schema, "value")
        self._validate_schema_requirements(key_schema_type, key_schema, "key")
        self._validate_prefix_length(value_schema_id_prefix_length, "value")
        self._validate_prefix_length(key_schema_id_prefix_length, "key")

        self.value_schema_type = value_schema_type
        self.value_schema = value_schema
        self.value_output_serializer = value_output_serializer
        self.key_schema_type = key_schema_type
        self.key_schema = key_schema
        self.key_output_serializer = key_output_serializer
        self.value_schema_id_prefix_length = value_schema_id_prefix_length
        self.key_schema_id_prefix_length = key_schema_id_prefix_length

    def _validate_schema_requirements(self, schema_type: str | None, schema: str | None, prefix: str) -> None:
        """Validate that schema is provided when required by schema_type."""
        if schema_type in ["AVRO", "PROTOBUF"] and schema is None:
            raise KafkaConsumerMissingSchemaError(
                f"{prefix}_schema must be provided when {prefix}_schema_type is {schema_type}",
            )

    def _validate_prefix_length(self, prefix_length: int, prefix: str) -> None:
        """Validate that a schema-id prefix length is a non-negative integer."""
        if not isinstance(prefix_length, int) or isinstance(prefix_length, bool) or prefix_length < 0:
            raise ValueError(
                f"{prefix}_schema_id_prefix_length must be a non-negative integer, got {prefix_length!r}",
            )
