from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.data_classes.common import CaseInsensitiveDict
from aws_lambda_powertools.utilities.data_classes.kafka_event import KafkaEvent, KafkaEventBase
from aws_lambda_powertools.utilities.kafka_consumer.deserializer.deserializer import get_deserializer
from aws_lambda_powertools.utilities.kafka_consumer.serialization.serialization import serialize_to_output_type

if TYPE_CHECKING:
    from collections.abc import Iterator

    from aws_lambda_powertools.utilities.kafka_consumer.schema_config import SchemaConfig


class ConsumerRecordRecords(KafkaEventBase):
    """
    A Kafka Consumer Record
    """

    def __init__(self, data: dict[str, Any], deserialize: SchemaConfig | None = None):
        super().__init__(data)
        self.deserialize = deserialize

    @property
    def key(self) -> Any:
        key = self.get("key")
        if key and (self.deserialize and self.deserialize.key_schema_type):
            deserializer = get_deserializer(
                self.deserialize.key_schema_type,
                self.deserialize.key_schema_str,
            )
            deserialized_key = deserializer.deserialize(key)

            if self.deserialize.key_output_serializer:
                return serialize_to_output_type(
                    deserialized_key,
                    self.deserialize.key_output_serializer,
                )

            return deserialized_key

        return key

    @property
    def value(self) -> Any:
        value = self["value"]
        if value and (self.deserialize and self.deserialize.value_schema_type):
            deserializer = get_deserializer(
                self.deserialize.value_schema_type,
                self.deserialize.value_schema_str,
            )
            deserialized_value = deserializer.deserialize(value)

            if self.deserialize.value_output_serializer:
                return serialize_to_output_type(
                    deserialized_value,
                    self.deserialize.value_output_serializer,
                )

            return deserialized_value

        return value

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
    def headers(self) -> list[dict[str, list[int]]]:
        """The raw Kafka record headers."""
        return CaseInsensitiveDict((k, bytes(v)) for chunk in self.headers for k, v in chunk.items())

    @property
    def original_headers(self) -> dict[str, bytes]:
        """Decodes the headers as a single dictionary."""
        return self["headers"]


class ConsumerRecords(KafkaEvent):
    """Self-managed or MSK Apache Kafka event trigger
    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-kafka.html
    - https://docs.aws.amazon.com/lambda/latest/dg/with-msk.html
    """

    def __init__(self, data: dict[str, Any], deserialize: SchemaConfig | None = None):
        super().__init__(data)
        self._records: Iterator[ConsumerRecordRecords] | None = None
        self.deserialize = deserialize

    @property
    def records(self) -> Iterator[ConsumerRecordRecords]:
        """The Kafka records."""
        for chunk in self["records"].values():
            for record in chunk:
                yield ConsumerRecordRecords(data=record, deserialize=self.deserialize)

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
