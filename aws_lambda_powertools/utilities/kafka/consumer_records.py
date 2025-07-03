from __future__ import annotations

import logging
from functools import cached_property
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.shared.functions import decode_header_bytes
from aws_lambda_powertools.utilities.data_classes.common import CaseInsensitiveDict
from aws_lambda_powertools.utilities.data_classes.kafka_event import KafkaEventBase, KafkaEventRecordBase
from aws_lambda_powertools.utilities.kafka.deserializer.deserializer import get_deserializer
from aws_lambda_powertools.utilities.kafka.serialization.serialization import serialize_to_output_type

if TYPE_CHECKING:
    from collections.abc import Iterator

    from aws_lambda_powertools.utilities.kafka.schema_config import SchemaConfig

logger = logging.getLogger(__name__)


class ConsumerRecordRecords(KafkaEventRecordBase):
    """
    A Kafka Consumer Record
    """

    def __init__(self, data: dict[str, Any], schema_config: SchemaConfig | None = None):
        super().__init__(data)
        self.schema_config = schema_config

    @cached_property
    def key(self) -> Any:
        key = self.get("key")

        # Return None if key doesn't exist
        if not key:
            return None

        logger.debug("Deserializing key field")

        # Determine schema type and schema string
        schema_type = None
        schema_value = None
        output_serializer = None

        if self.schema_config and self.schema_config.key_schema_type:
            schema_type = self.schema_config.key_schema_type
            schema_value = self.schema_config.key_schema
            output_serializer = self.schema_config.key_output_serializer

        # Always use get_deserializer if None it will default to DEFAULT
        deserializer = get_deserializer(
            schema_type=schema_type,
            schema_value=schema_value,
            field_metadata=self.key_schema_metadata,
        )
        deserialized_value = deserializer.deserialize(key)

        # Apply output serializer if specified
        if output_serializer:
            return serialize_to_output_type(deserialized_value, output_serializer)

        return deserialized_value

    @cached_property
    def value(self) -> Any:
        value = self["value"]

        # Determine schema type and schema string
        schema_type = None
        schema_value = None
        output_serializer = None

        logger.debug("Deserializing value field")

        if self.schema_config and self.schema_config.value_schema_type:
            schema_type = self.schema_config.value_schema_type
            schema_value = self.schema_config.value_schema
            output_serializer = self.schema_config.value_output_serializer

        # Always use get_deserializer if None it will default to DEFAULT
        deserializer = get_deserializer(
            schema_type=schema_type,
            schema_value=schema_value,
            field_metadata=self.value_schema_metadata,
        )
        deserialized_value = deserializer.deserialize(value)

        # Apply output serializer if specified
        if output_serializer:
            return serialize_to_output_type(deserialized_value, output_serializer)

        return deserialized_value

    @property
    def original_value(self) -> str:
        """The original (base64 encoded) Kafka record value."""
        return self["value"]

    @property
    def original_key(self) -> str | None:
        """
        The original (base64 encoded) Kafka record key.

        This key is optional; if not provided,
        a round-robin algorithm will be used to determine
        the partition for the message.
        """

        return self.get("key")

    @property
    def original_headers(self) -> list[dict[str, list[int]]]:
        """The raw Kafka record headers."""
        return self["headers"]

    @cached_property
    def headers(self) -> dict[str, bytes]:
        """Decodes the headers as a single dictionary."""
        return CaseInsensitiveDict(
            (k, decode_header_bytes(v)) for chunk in self.original_headers for k, v in chunk.items()
        )


class ConsumerRecords(KafkaEventBase):
    """Self-managed or MSK Apache Kafka event trigger
    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-kafka.html
    - https://docs.aws.amazon.com/lambda/latest/dg/with-msk.html
    """

    def __init__(self, data: dict[str, Any], schema_config: SchemaConfig | None = None):
        super().__init__(data)
        self._records: Iterator[ConsumerRecordRecords] | None = None
        self.schema_config = schema_config

    @property
    def records(self) -> Iterator[ConsumerRecordRecords]:
        """The Kafka records."""
        for chunk in self["records"].values():
            for record in chunk:
                yield ConsumerRecordRecords(data=record, schema_config=self.schema_config)

    @property
    def record(self) -> ConsumerRecordRecords:
        """
        Returns the next Kafka record using an iterator.

        Returns
        -------
        ConsumerRecordRecords
            The next Kafka record.

        Raises
        ------
        StopIteration
            If there are no more records available.

        """
        if self._records is None:
            self._records = self.records
        return next(self._records)
