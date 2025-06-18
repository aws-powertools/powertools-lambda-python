import base64
import json
from copy import deepcopy
from dataclasses import dataclass

import pytest

from aws_lambda_powertools.utilities.kafka_consumer.consumer_records import ConsumerRecords
from aws_lambda_powertools.utilities.kafka_consumer.exceptions import (
    KafkaConsumerDeserializationError,
)
from aws_lambda_powertools.utilities.kafka_consumer.kafka_consumer import kafka_consumer
from aws_lambda_powertools.utilities.kafka_consumer.schema_config import SchemaConfig


@pytest.fixture
def json_encoded_value():
    data = {"name": "John Doe", "age": 30}
    return base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")


@pytest.fixture
def json_encoded_key():
    data = {"user_id": "123"}
    return base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")


@pytest.fixture
def kafka_event_with_json_data(json_encoded_value, json_encoded_key):
    return {
        "eventSource": "aws:kafka",
        "eventSourceArn": "arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster/abcdefg",
        "records": {
            "my-topic-1": [
                {
                    "topic": "my-topic-1",
                    "partition": 0,
                    "offset": 15,
                    "timestamp": 1545084650987,
                    "timestampType": "CREATE_TIME",
                    "key": json_encoded_key,
                    "value": json_encoded_value,
                    "headers": [{"headerKey": [104, 101, 97, 100, 101, 114, 86, 97, 108, 117, 101]}],
                },
            ],
        },
    }


@dataclass
class UserValueDataClass:
    name: str
    age: int


@dataclass
class UserKeyClass:
    user_id: str


def test_kafka_consumer_with_json(kafka_event_with_json_data, lambda_context):
    """Test Kafka consumer with JSON deserialization without output serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(value_schema_type="JSON")

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        record = next(event.records)
        result_data["value_type"] = type(record.value).__name__
        result_data["name"] = record.value["name"]
        result_data["age"] = record.value["age"]
        return {"processed": True}

    # Call the handler
    result = handler(kafka_event_with_json_data, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert result_data["value_type"] == "dict"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_json_and_dataclass(kafka_event_with_json_data, lambda_context):
    """Test Kafka consumer with JSON deserialization and dataclass output serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=UserValueDataClass)

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        record = next(event.records)
        result_data["value_type"] = type(record.value).__name__
        result_data["name"] = record.value.name
        result_data["age"] = record.value.age
        return {"processed": True}

    # Call the handler
    result = handler(kafka_event_with_json_data, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert result_data["value_type"] == "UserValueDataClass"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_invalid_json_data(kafka_event_with_json_data, lambda_context):
    """Test error handling when JSON data is invalid."""

    # Create invalid JSON data
    invalid_data = "invalid json data"
    kafka_event_with_json_data = deepcopy(kafka_event_with_json_data)
    kafka_event_with_json_data["records"]["my-topic-1"][0]["value"] = invalid_data

    schema_config = SchemaConfig(value_schema_type="JSON")

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # This should never be reached if deserializer fails
        record = next(event.records)
        assert record.value
        return {"processed": True}

    # This should raise a deserialization error
    with pytest.raises(KafkaConsumerDeserializationError) as excinfo:
        handler(kafka_event_with_json_data, lambda_context)

    assert "Error trying to deserialize json data" in str(excinfo.value)


# Tests for Complex Types with Pydantic TypeAdapter
def test_kafka_consumer_with_multiple_records(lambda_context):
    """Test processing multiple records in a single event."""

    # Create data for multiple records
    data1 = {"name": "John Doe", "age": 30}
    data2 = {"name": "Jane Smith", "age": 25}
    data3 = {"name": "Bob Johnson", "age": 40}

    # Encode the data
    encoded1 = base64.b64encode(json.dumps(data1).encode("utf-8")).decode("utf-8")
    encoded2 = base64.b64encode(json.dumps(data2).encode("utf-8")).decode("utf-8")
    encoded3 = base64.b64encode(json.dumps(data3).encode("utf-8")).decode("utf-8")

    # Create a kafka event with multiple records
    multi_record_event = {
        "eventSource": "aws:kafka",
        "records": {
            "my-topic-1": [
                {
                    "topic": "my-topic-1",
                    "partition": 0,
                    "offset": 15,
                    "timestamp": 1545084650987,
                    "timestampType": "CREATE_TIME",
                    "key": None,
                    "value": encoded1,
                    "headers": [],
                },
                {
                    "topic": "my-topic-1",
                    "partition": 0,
                    "offset": 16,
                    "timestamp": 1545084651987,
                    "timestampType": "CREATE_TIME",
                    "key": None,
                    "value": encoded2,
                    "headers": [],
                },
                {
                    "topic": "my-topic-1",
                    "partition": 0,
                    "offset": 17,
                    "timestamp": 1545084652987,
                    "timestampType": "CREATE_TIME",
                    "key": None,
                    "value": encoded3,
                    "headers": [],
                },
            ],
        },
    }

    # Create schema config
    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=UserValueDataClass)

    # Create list to store processed records
    processed_records = []

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Process all records
        for record in event.records:
            processed_records.append({"name": record.value.name, "age": record.value.age})
        return {"processed": len(processed_records)}

    # Call the handler
    result = handler(multi_record_event, lambda_context)

    # Verify the results
    assert result == {"processed": 3}
    assert len(processed_records) == 3
    assert any(r["name"] == "John Doe" and r["age"] == 30 for r in processed_records)
    assert any(r["name"] == "Jane Smith" and r["age"] == 25 for r in processed_records)
    assert any(r["name"] == "Bob Johnson" and r["age"] == 40 for r in processed_records)


def test_kafka_consumer_default_deserializer_value(kafka_event_with_json_data, lambda_context):
    """Test Kafka consumer when no schema config is provided."""

    base64_data = base64.b64encode(b"data")
    kafka_event_with_json_data = deepcopy(kafka_event_with_json_data)
    kafka_event_with_json_data["records"]["my-topic-1"][0]["value"] = base64_data

    @kafka_consumer()
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        record = next(event.records)
        # Should get raw base64-encoded data with no deserialization
        return record.value

    # Call the handler
    result = handler(kafka_event_with_json_data, lambda_context)

    # Verify the results
    assert result == "data"


def test_kafka_consumer_default_deserializer_key(kafka_event_with_json_data, lambda_context):
    """Test Kafka consumer when no schema config is provided."""

    base64_data = base64.b64encode(b"data")
    kafka_event_with_json_data = deepcopy(kafka_event_with_json_data)
    kafka_event_with_json_data["records"]["my-topic-1"][0]["key"] = base64_data

    @kafka_consumer()
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        record = next(event.records)
        # Should get raw base64-encoded data with no deserialization
        return record.key

    # Call the handler
    result = handler(kafka_event_with_json_data, lambda_context)

    # Verify the results
    assert result == "data"


def test_kafka_consumer_default_deserializer_key_is_none(kafka_event_with_json_data, lambda_context):
    """Test Kafka consumer when no schema config is provided."""

    kafka_event_with_json_data["records"]["my-topic-1"][0]["key"] = None

    @kafka_consumer()
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        record = next(event.records)
        # Should get raw base64-encoded data with no deserialization
        return record.key

    # Call the handler
    result = handler(kafka_event_with_json_data, lambda_context)

    # Verify the results
    assert result is None
