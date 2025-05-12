from __future__ import annotations

from typing import Any

from aws_lambda_powertools.utilities.data_classes.kafka_event import KafkaEventRecord


class ConsumerRecord(KafkaEventRecord):
    """
    A Kafka Consumer Record
    """

    def __init__(self, data: dict[str, Any], json_deserializer=None):
        super().__init__(data, json_deserializer=json_deserializer)
        self._json_deserializer = json_deserializer
