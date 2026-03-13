"""Tests for Kafka batch processing support."""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING, Any

import pytest

from aws_lambda_powertools.utilities.batch import (
    AsyncBatchProcessor,
    BatchProcessor,
    EventType,
    async_process_partial_response,
    process_partial_response,
)
from aws_lambda_powertools.utilities.batch.exceptions import BatchProcessingError, UnexpectedBatchTypeError
from aws_lambda_powertools.utilities.data_classes.kafka_event import KafkaEventRecord  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


def str_to_b64(value: str) -> str:
    """Convert string to base64 encoded string."""
    return base64.b64encode(value.encode()).decode()


@pytest.fixture(scope="module")
def kafka_event_factory() -> Callable:
    """Factory for creating Kafka event records."""

    def factory(body: str, topic: str = "mytopic", partition: int = 0, offset: int = 0):
        return {
            "topic": topic,
            "partition": partition,
            "offset": offset,
            "timestamp": 1545084650987,
            "timestampType": "CREATE_TIME",
            "key": str_to_b64("recordKey"),
            "value": str_to_b64(body),
            "headers": [{"headerKey": [104, 101, 97, 100, 101, 114, 86, 97, 108, 117, 101]}],
        }

    return factory


@pytest.fixture(scope="module")
def kafka_record_handler() -> Callable:
    """Handler for Kafka records that fails if body contains 'fail'."""

    def handler(record: KafkaEventRecord):
        body = record.decoded_value.decode("utf-8")
        if "fail" in body:
            raise Exception("Failed to process record.")
        return body

    return handler


@pytest.fixture(scope="module")
def async_kafka_record_handler() -> Callable[..., Awaitable[Any]]:
    """Async handler for Kafka records that fails if body contains 'fail'."""

    async def handler(record: KafkaEventRecord):
        body = record.decoded_value.decode("utf-8")
        if "fail" in body:
            raise Exception("Failed to process record.")
        return body

    return handler


def build_kafka_event(records: list[dict], topic_partition: str = "mytopic-0") -> dict:
    """Build a complete Kafka event from records."""
    return {
        "eventSource": "aws:kafka",
        "eventSourceArn": "arn:aws:kafka:us-east-1:123456789012:cluster/MyCluster/abc123",
        "bootstrapServers": "b-1.cluster.kafka.us-east-1.amazonaws.com:9092",
        "records": {topic_partition: records},
    }


def build_multi_topic_kafka_event(records_by_topic: dict[str, list[dict]]) -> dict:
    """Build a Kafka event with multiple topic-partitions."""
    return {
        "eventSource": "aws:kafka",
        "eventSourceArn": "arn:aws:kafka:us-east-1:123456789012:cluster/MyCluster/abc123",
        "bootstrapServers": "b-1.cluster.kafka.us-east-1.amazonaws.com:9092",
        "records": records_by_topic,
    }


class TestKafkaBatchProcessing:
    """Test Kafka batch processing with process_partial_response."""

    def test_kafka_batch_processor_success_only(self, kafka_event_factory, kafka_record_handler):
        """Test successful processing of all Kafka records."""
        # GIVEN
        first_record = kafka_event_factory("success", offset=0)
        second_record = kafka_event_factory("success", offset=1)
        event = build_kafka_event([first_record, second_record])

        processor = BatchProcessor(event_type=EventType.Kafka)

        # WHEN
        result = process_partial_response(
            event=event,
            record_handler=kafka_record_handler,
            processor=processor,
        )

        # THEN
        assert result["batchItemFailures"] == []

    def test_kafka_batch_processor_failure_only(self, kafka_event_factory, kafka_record_handler):
        """Test processing where all Kafka records fail."""
        # GIVEN
        first_record = kafka_event_factory("fail", offset=0)
        second_record = kafka_event_factory("fail", offset=1)
        event = build_kafka_event([first_record, second_record])

        processor = BatchProcessor(event_type=EventType.Kafka)

        # WHEN/THEN - entire batch failure should raise
        with pytest.raises(BatchProcessingError):
            process_partial_response(
                event=event,
                record_handler=kafka_record_handler,
                processor=processor,
            )

    def test_kafka_batch_processor_partial_failure(self, kafka_event_factory, kafka_record_handler):
        """Test partial failure processing for Kafka records."""
        # GIVEN
        success_record = kafka_event_factory("success", offset=0)
        fail_record = kafka_event_factory("fail", topic="mytopic", partition=0, offset=1)
        event = build_kafka_event([success_record, fail_record])

        processor = BatchProcessor(event_type=EventType.Kafka)

        # WHEN
        result = process_partial_response(
            event=event,
            record_handler=kafka_record_handler,
            processor=processor,
        )

        # THEN - Kafka uses composite identifier
        assert len(result["batchItemFailures"]) == 1
        assert result["batchItemFailures"][0]["itemIdentifier"] == {
            "partition": "mytopic-0",
            "offset": 1,
        }

    def test_kafka_batch_processor_multiple_failures(self, kafka_event_factory, kafka_record_handler):
        """Test multiple failures in Kafka batch."""
        # GIVEN
        success_record = kafka_event_factory("success", offset=0)
        fail_record_1 = kafka_event_factory("fail", offset=1)
        fail_record_2 = kafka_event_factory("fail", offset=2)
        event = build_kafka_event([success_record, fail_record_1, fail_record_2])

        processor = BatchProcessor(event_type=EventType.Kafka)

        # WHEN
        result = process_partial_response(
            event=event,
            record_handler=kafka_record_handler,
            processor=processor,
        )

        # THEN
        assert len(result["batchItemFailures"]) == 2
        offsets = [f["itemIdentifier"]["offset"] for f in result["batchItemFailures"]]
        assert 1 in offsets
        assert 2 in offsets

    def test_kafka_batch_processor_multi_topic_partition(self, kafka_event_factory, kafka_record_handler):
        """Test processing records from multiple topic-partitions."""
        # GIVEN
        topic1_success = kafka_event_factory("success", topic="topic1", partition=0, offset=0)
        topic1_fail = kafka_event_factory("fail", topic="topic1", partition=0, offset=1)
        topic2_success = kafka_event_factory("success", topic="topic2", partition=1, offset=0)
        topic2_fail = kafka_event_factory("fail", topic="topic2", partition=1, offset=1)

        event = build_multi_topic_kafka_event(
            {
                "topic1-0": [topic1_success, topic1_fail],
                "topic2-1": [topic2_success, topic2_fail],
            },
        )

        processor = BatchProcessor(event_type=EventType.Kafka)

        # WHEN
        result = process_partial_response(
            event=event,
            record_handler=kafka_record_handler,
            processor=processor,
        )

        # THEN
        assert len(result["batchItemFailures"]) == 2
        topic_partitions = [f["itemIdentifier"]["partition"] for f in result["batchItemFailures"]]
        assert "topic1-0" in topic_partitions
        assert "topic2-1" in topic_partitions

    def test_kafka_batch_processor_with_json_body(self, kafka_event_factory):
        """Test processing Kafka records with JSON body."""
        # GIVEN
        json_body = json.dumps({"message": "hello", "status": "success"})
        record = kafka_event_factory(json_body, offset=0)
        event = build_kafka_event([record])

        processor = BatchProcessor(event_type=EventType.Kafka)

        def json_record_handler(record: KafkaEventRecord):
            data = record.json_value
            return data["message"]

        # WHEN
        result = process_partial_response(
            event=event,
            record_handler=json_record_handler,
            processor=processor,
        )

        # THEN
        assert result["batchItemFailures"] == []

    def test_kafka_batch_processor_disable_raise_on_entire_batch_failure(
        self,
        kafka_event_factory,
        kafka_record_handler,
    ):
        """Test that entire batch failure can be suppressed."""
        # GIVEN
        first_record = kafka_event_factory("fail", offset=0)
        second_record = kafka_event_factory("fail", offset=1)
        event = build_kafka_event([first_record, second_record])

        processor = BatchProcessor(event_type=EventType.Kafka, raise_on_entire_batch_failure=False)

        # WHEN
        result = process_partial_response(
            event=event,
            record_handler=kafka_record_handler,
            processor=processor,
        )

        # THEN
        assert len(result["batchItemFailures"]) == 2

    def test_kafka_batch_processor_invalid_event_structure(self, kafka_record_handler):
        """Test that invalid Kafka event structure raises appropriate error."""
        # GIVEN - Invalid event with empty records
        event = {
            "eventSource": "aws:kafka",
            "records": {},
        }

        processor = BatchProcessor(event_type=EventType.Kafka)

        # WHEN/THEN
        with pytest.raises(UnexpectedBatchTypeError) as exc_info:
            process_partial_response(
                event=event,
                record_handler=kafka_record_handler,
                processor=processor,
            )

        assert "Invalid Kafka event structure" in str(exc_info.value)

    def test_kafka_batch_processor_missing_records_key(self, kafka_record_handler):
        """Test that missing records key raises appropriate error."""
        # GIVEN
        event = {
            "eventSource": "aws:kafka",
        }

        processor = BatchProcessor(event_type=EventType.Kafka)

        # WHEN/THEN
        with pytest.raises(UnexpectedBatchTypeError):
            process_partial_response(
                event=event,
                record_handler=kafka_record_handler,
                processor=processor,
            )


class TestAsyncKafkaBatchProcessing:
    """Test async Kafka batch processing with async_process_partial_response."""

    def test_async_kafka_batch_processor_success_only(self, kafka_event_factory, async_kafka_record_handler):
        """Test successful async processing of all Kafka records."""
        # GIVEN
        first_record = kafka_event_factory("success", offset=0)
        second_record = kafka_event_factory("success", offset=1)
        event = build_kafka_event([first_record, second_record])

        processor = AsyncBatchProcessor(event_type=EventType.Kafka)

        # WHEN
        result = async_process_partial_response(
            event=event,
            record_handler=async_kafka_record_handler,
            processor=processor,
        )

        # THEN
        assert result["batchItemFailures"] == []

    def test_async_kafka_batch_processor_partial_failure(self, kafka_event_factory, async_kafka_record_handler):
        """Test async partial failure processing for Kafka records."""
        # GIVEN
        success_record = kafka_event_factory("success", offset=0)
        fail_record = kafka_event_factory("fail", offset=1)
        event = build_kafka_event([success_record, fail_record])

        processor = AsyncBatchProcessor(event_type=EventType.Kafka)

        # WHEN
        result = async_process_partial_response(
            event=event,
            record_handler=async_kafka_record_handler,
            processor=processor,
        )

        # THEN
        assert len(result["batchItemFailures"]) == 1
        assert result["batchItemFailures"][0]["itemIdentifier"] == {
            "partition": "mytopic-0",
            "offset": 1,
        }

    def test_async_kafka_batch_processor_failure_only(self, kafka_event_factory, async_kafka_record_handler):
        """Test async processing where all Kafka records fail."""
        # GIVEN
        first_record = kafka_event_factory("fail", offset=0)
        second_record = kafka_event_factory("fail", offset=1)
        event = build_kafka_event([first_record, second_record])

        processor = AsyncBatchProcessor(event_type=EventType.Kafka)

        # WHEN/THEN
        with pytest.raises(BatchProcessingError):
            async_process_partial_response(
                event=event,
                record_handler=async_kafka_record_handler,
                processor=processor,
            )


class TestKafkaContextManager:
    """Test Kafka batch processing using context manager pattern."""

    def test_kafka_batch_processor_context_manager(self, kafka_event_factory, kafka_record_handler):
        """Test Kafka batch processing using context manager."""
        # GIVEN
        success_record = kafka_event_factory("success", offset=0)
        fail_record = kafka_event_factory("fail", offset=1)
        event = build_kafka_event([success_record, fail_record])

        processor = BatchProcessor(event_type=EventType.Kafka)

        # Flatten records manually (mimicking what process_partial_response does)
        records = [r for topic_records in event["records"].values() for r in topic_records]

        # WHEN
        with processor(records, kafka_record_handler):
            processor.process()

        result = processor.response()

        # THEN
        assert len(result["batchItemFailures"]) == 1
        assert result["batchItemFailures"][0]["itemIdentifier"]["offset"] == 1


class TestKafkaRecordDataClass:
    """Test KafkaEventRecord data class integration with batch processor."""

    def test_kafka_record_properties_accessible(self, kafka_event_factory):
        """Test that Kafka record properties are accessible in handler."""
        # GIVEN
        record_data = kafka_event_factory("test message", topic="test-topic", partition=5, offset=100)
        event = build_kafka_event([record_data], topic_partition="test-topic-5")

        processor = BatchProcessor(event_type=EventType.Kafka)
        captured_record = None

        def capture_handler(record: KafkaEventRecord):
            nonlocal captured_record
            captured_record = record
            return "processed"

        # WHEN
        process_partial_response(
            event=event,
            record_handler=capture_handler,
            processor=processor,
        )

        # THEN
        assert captured_record is not None
        assert captured_record.topic == "test-topic"
        assert captured_record.partition == 5
        assert captured_record.offset == 100
        assert captured_record.timestamp == 1545084650987
        assert captured_record.timestamp_type == "CREATE_TIME"
