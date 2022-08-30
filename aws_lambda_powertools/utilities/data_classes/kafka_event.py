from base64 import b64decode
from typing import Dict, Iterator

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class KafkaEventRecord(DictWrapper):
    @property
    def topic(self) -> str:
        """The Kafka topic."""
        return self["topic"]

    @property
    def partition(self) -> str:
        """The Kafka record parition."""
        return self["partition"]

    @property
    def offset(self) -> str:
        """The Kafka record offset."""
        return self["offset"]

    @property
    def timestamp(self) -> int:
        """The Kafka record timestamp."""
        return self["timestamp"]

    @property
    def timestamp_type(self) -> str:
        """The Kafka record timestamp type."""
        return self["timestamp_type"]

    @property
    def key(self) -> bytes:
        """The base64 decoded Kafka record key."""
        return b64decode(self.key)

    @property
    def value(self) -> bytes:
        """The base64 decoded Kafka record value."""
        return b64decode(self.value)

    @property
    def headers(self) -> Dict[str, bytes]:
        """The decoded Kafka record headers."""
        headers = {}
        for chunk in self["headers"]:
            for key, val in chunk.items():
                headers[key] = bytes(val)
        return headers


class KafkaEvent(DictWrapper):
    """Self-managed Apache Kafka event trigger
    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-kafka.html
    """

    @property
    def event_source(self) -> str:
        """The AWS service from which the Kafka event record originated."""
        return self["eventSource"]

    @property
    def event_source_arn(self) -> str:
        """The AWS service ARN from which the Kafka event record originated."""
        return self["eventSourceArn"]

    @property
    def bootstrap_servers(self) -> str:
        """The Kafka bootstrap URL."""
        return self["bootstrapServers"]

    @property
    def records(self) -> Iterator[KafkaEventRecord]:
        """The Kafka records."""
        for chunk in self["records"].values():
            for record in chunk:
                yield KafkaEventRecord(record)

    @property
    def record(self) -> KafkaEventRecord:
        """The next Kafka record."""
        return next(self.records)
