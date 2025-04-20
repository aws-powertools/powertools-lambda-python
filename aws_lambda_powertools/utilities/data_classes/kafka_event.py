from __future__ import annotations

import base64
from functools import cached_property
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.data_classes.common import CaseInsensitiveDict, DictWrapper

if TYPE_CHECKING:
    from collections.abc import Iterator


class KafkaEventRecord(DictWrapper):
    @property
    def topic(self) -> str:
        """The Kafka topic."""
        return self["topic"]

    @property
    def partition(self) -> int:
        """The Kafka record parition."""
        return self["partition"]

    @property
    def offset(self) -> int:
        """The Kafka record offset."""
        return self["offset"]

    @property
    def timestamp(self) -> int:
        """The Kafka record timestamp."""
        return self["timestamp"]

    @property
    def timestamp_type(self) -> str:
        """The Kafka record timestamp type."""
        return self["timestampType"]

    @property
    def key(self) -> str | None:
        """
        The raw (base64 encoded) Kafka record key.

        This key is optional; if not provided,
        a round-robin algorithm will be used to determine
        the partition for the message.
        """

        return self.get("key")

    @property
    def decoded_key(self) -> bytes | None:
        """
        Decode the base64 encoded key as bytes.

        If the key is not provided, this will return None.
        """
        return None if self.key is None else base64.b64decode(self.key)

    @property
    def value(self) -> str:
        """The raw (base64 encoded) Kafka record value."""
        return self["value"]

    @property
    def decoded_value(self) -> bytes:
        """Decodes the base64 encoded value as bytes."""
        return base64.b64decode(self.value)

    @cached_property
    def json_value(self) -> Any:
        """Decodes the text encoded data as JSON."""
        return self._json_deserializer(self.decoded_value.decode("utf-8"))

    @property
    def headers(self) -> list[dict[str, list[int]]]:
        """The raw Kafka record headers."""
        return self["headers"]

    @cached_property
    def decoded_headers(self) -> dict[str, bytes]:
        """Decodes the headers as a single dictionary."""
        return CaseInsensitiveDict((k, bytes(v)) for chunk in self.headers for k, v in chunk.items())


class KafkaEvent(DictWrapper):
    """Self-managed or MSK Apache Kafka event trigger
    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-kafka.html
    - https://docs.aws.amazon.com/lambda/latest/dg/with-msk.html
    """

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self._records: Iterator[KafkaEventRecord] | None = None

    @property
    def event_source(self) -> str:
        """The AWS service from which the Kafka event record originated."""
        return self["eventSource"]

    @property
    def event_source_arn(self) -> str | None:
        """The AWS service ARN from which the Kafka event record originated, mandatory for AWS MSK."""
        return self.get("eventSourceArn")

    @property
    def bootstrap_servers(self) -> str:
        """The Kafka bootstrap URL."""
        return self["bootstrapServers"]

    @property
    def decoded_bootstrap_servers(self) -> list[str]:
        """The decoded Kafka bootstrap URL."""
        return self.bootstrap_servers.split(",")

    @property
    def records(self) -> Iterator[KafkaEventRecord]:
        """The Kafka records."""
        for chunk in self["records"].values():
            for record in chunk:
                yield KafkaEventRecord(data=record, json_deserializer=self._json_deserializer)

    @property
    def record(self) -> KafkaEventRecord:
        """
        Returns the next Kafka record using an iterator.

        Returns
        -------
        KafkaEventRecord
            The next Kafka record.

        Raises
        ------
        StopIteration
            If there are no more records available.

        """
        if self._records is None:
            self._records = self.records
        return next(self._records)
