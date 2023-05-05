import base64
from typing import Any, Dict, Iterator, List, Optional

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
        return self["timestampType"]

    @property
    def key(self) -> str:
        """The raw (base64 encoded) Kafka record key."""
        return self["key"]

    @property
    def decoded_key(self) -> bytes:
        """Decode the base64 encoded key as bytes."""
        return base64.b64decode(self.key)

    @property
    def value(self) -> str:
        """The raw (base64 encoded) Kafka record value."""
        return self["value"]

    @property
    def decoded_value(self) -> bytes:
        """Decodes the base64 encoded value as bytes."""
        return base64.b64decode(self.value)

    @property
    def json_value(self) -> Any:
        """Decodes the text encoded data as JSON."""
        if self._json_data is None:
            self._json_data = self._json_deserializer(self.decoded_value.decode("utf-8"))
        return self._json_data

    @property
    def headers(self) -> List[Dict[str, List[int]]]:
        """The raw Kafka record headers."""
        return self["headers"]

    @property
    def decoded_headers(self) -> Dict[str, bytes]:
        """Decodes the headers as a single dictionary."""
        return {k: bytes(v) for chunk in self.headers for k, v in chunk.items()}

    def get_header_value(
        self, name: str, default_value: Optional[Any] = None, case_sensitive: bool = True
    ) -> Optional[bytes]:
        """Get a decoded header value by name."""
        if case_sensitive:
            return self.decoded_headers.get(name, default_value)
        name_lower = name.lower()

        return next(
            # Iterate over the dict and do a case-insensitive key comparison
            (value for key, value in self.decoded_headers.items() if key.lower() == name_lower),
            # Default value is returned if no matches was found
            default_value,
        )


class KafkaEvent(DictWrapper):
    """Self-managed or MSK Apache Kafka event trigger
    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-kafka.html
    - https://docs.aws.amazon.com/lambda/latest/dg/with-msk.html
    """

    @property
    def event_source(self) -> str:
        """The AWS service from which the Kafka event record originated."""
        return self["eventSource"]

    @property
    def event_source_arn(self) -> Optional[str]:
        """The AWS service ARN from which the Kafka event record originated, mandatory for AWS MSK."""
        return self.get("eventSourceArn")

    @property
    def bootstrap_servers(self) -> str:
        """The Kafka bootstrap URL."""
        return self["bootstrapServers"]

    @property
    def decoded_bootstrap_servers(self) -> List[str]:
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
        """The next Kafka record."""
        return next(self.records)
