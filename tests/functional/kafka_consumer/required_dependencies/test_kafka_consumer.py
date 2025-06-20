import base64
import json
from copy import deepcopy
from dataclasses import dataclass

import pytest

from aws_lambda_powertools.utilities.kafka.consumer_records import ConsumerRecords
from aws_lambda_powertools.utilities.kafka.exceptions import (
    KafkaConsumerDeserializationError,
    KafkaConsumerDeserializationFormatMismatch,
)
from aws_lambda_powertools.utilities.kafka.kafka_consumer import kafka_consumer
from aws_lambda_powertools.utilities.kafka.schema_config import SchemaConfig


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
    # GIVEN
    # A Kafka consumer configured to deserialize JSON data
    # without any additional output serialization
    schema_config = SchemaConfig(value_schema_type="JSON")

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Return the deserialized JSON value for verification
        return event.record.value

    # WHEN
    # The handler processes a Kafka event containing JSON-encoded data
    result = handler(kafka_event_with_json_data, lambda_context)

    # THEN
    # The JSON should be correctly deserialized into a Python dictionary
    # with the expected field values
    assert result["name"] == "John Doe"
    assert result["age"] == 30


def test_kafka_consumer_with_json_and_dataclass(kafka_event_with_json_data, lambda_context):
    # GIVEN
    # A Kafka consumer configured to deserialize JSON data
    # and convert it to a UserValueDataClass instance
    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=UserValueDataClass)

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Extract the deserialized and serialized value
        # which should be a UserValueDataClass instance
        value: UserValueDataClass = event.record.value
        return value

    # WHEN
    # The handler processes a Kafka event containing JSON-encoded data
    # which is deserialized into a dictionary and then converted to a dataclass
    result = handler(kafka_event_with_json_data, lambda_context)

    # THEN
    # The result should be a UserValueDataClass instance
    # with the correct property values from the original JSON
    assert isinstance(result, UserValueDataClass)
    assert result.name == "John Doe"
    assert result.age == 30


def test_kafka_consumer_with_invalid_json_data(kafka_event_with_json_data, lambda_context):
    # GIVEN
    # A Kafka event with raw string data that is not valid base64-encoded JSON
    invalid_data = "invalid json data"
    kafka_event_with_json_data = deepcopy(kafka_event_with_json_data)
    kafka_event_with_json_data["records"]["my-topic-1"][0]["value"] = invalid_data

    schema_config = SchemaConfig(value_schema_type="JSON")

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        return event.record.value

    # WHEN/THEN
    # The handler should fail to process the invalid JSON data
    # and raise a specific deserialization error
    with pytest.raises(KafkaConsumerDeserializationError) as excinfo:
        handler(kafka_event_with_json_data, lambda_context)

    # Ensure the error contains useful diagnostic information
    assert "Error trying to deserialize json data" in str(excinfo.value)


def test_kafka_consumer_with_multiple_records_json(lambda_context):
    # GIVEN
    # Three different user records to process
    # First user: John Doe, age 30
    data1 = {"name": "John Doe", "age": 30}
    # Second user: Jane Smith, age 25
    data2 = {"name": "Jane Smith", "age": 25}
    # Third user: Bob Johnson, age 40
    data3 = {"name": "Bob Johnson", "age": 40}

    # Base64-encoded JSON data for each record
    encoded1 = base64.b64encode(json.dumps(data1).encode("utf-8")).decode("utf-8")
    encoded2 = base64.b64encode(json.dumps(data2).encode("utf-8")).decode("utf-8")
    encoded3 = base64.b64encode(json.dumps(data3).encode("utf-8")).decode("utf-8")

    # A Kafka event containing multiple records across different offsets
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

    # A list to capture processed record details
    processed_records = []

    # A Kafka consumer configured to deserialize JSON and convert to dataclass instances
    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=UserValueDataClass)

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Process each record and collect its properties
        for record in event.records:
            processed_records.append({"name": record.value.name, "age": record.value.age})
        return {"processed": len(processed_records)}

    # WHEN
    # The handler processes the Kafka event containing multiple JSON records
    result = handler(multi_record_event, lambda_context)

    # THEN
    # The handler should successfully process all three records
    # and return the correct count
    assert result == {"processed": 3}
    assert len(processed_records) == 3

    # All three users should be correctly deserialized into dataclass instances
    # and their properties should be accessible
    assert any(r["name"] == "John Doe" and r["age"] == 30 for r in processed_records)
    assert any(r["name"] == "Jane Smith" and r["age"] == 25 for r in processed_records)
    assert any(r["name"] == "Bob Johnson" and r["age"] == 40 for r in processed_records)


def test_kafka_consumer_default_deserializer_value(kafka_event_with_json_data, lambda_context):
    # GIVEN
    # A simple string message encoded in base64
    raw_data = b"data"
    base64_data = base64.b64encode(raw_data).decode("utf-8")

    # A Kafka event with the base64-encoded data as value
    basic_kafka_event = deepcopy(kafka_event_with_json_data)
    basic_kafka_event["records"]["my-topic-1"][0]["value"] = base64_data

    # A Kafka consumer with no schema configuration specified
    # which should default to base64 decoding only
    @kafka_consumer()
    def handler(event: ConsumerRecords, context):
        # Get the first record's value
        record = next(event.records)
        # Should receive UTF-8 decoded data with no further processing
        return record.value

    # WHEN
    # The handler processes the Kafka event with default deserializer
    result = handler(basic_kafka_event, lambda_context)

    # THEN
    # The result should be the UTF-8 decoded string from the base64 data
    # with no additional deserialization applied
    assert result == "data"
    assert isinstance(result, str)


def test_kafka_consumer_default_deserializer_key(kafka_event_with_json_data, lambda_context):
    # GIVEN
    # A simple string message encoded in base64 for the key
    raw_key_data = b"data"
    base64_key = base64.b64encode(raw_key_data).decode("utf-8")

    # A Kafka event with the base64-encoded data as key
    kafka_event_with_key = deepcopy(kafka_event_with_json_data)
    kafka_event_with_key["records"]["my-topic-1"][0]["key"] = base64_key

    # A Kafka consumer with no schema configuration specified
    # which should default to base64 decoding only
    @kafka_consumer()
    def handler(event: ConsumerRecords, context):
        # Get the first record's key
        record = next(event.records)
        # Should receive UTF-8 decoded key with no further processing
        return record.key

    # WHEN
    # The handler processes the Kafka event with default key deserializer
    result = handler(kafka_event_with_key, lambda_context)

    # THEN
    # The key should be the UTF-8 decoded string from the base64 data
    # with no additional deserialization or transformation applied
    assert result == "data"
    assert isinstance(result, str)


def test_kafka_consumer_default_deserializer_key_is_none(kafka_event_with_json_data, lambda_context):
    # GIVEN
    # A Kafka event with a null key in the record
    kafka_event_with_null_key = deepcopy(kafka_event_with_json_data)
    kafka_event_with_null_key["records"]["my-topic-1"][0]["key"] = None

    # A Kafka consumer with no schema configuration specified
    @kafka_consumer()
    def handler(event: ConsumerRecords, context):
        # Get the first record's key which should be None
        record = next(event.records)
        return record.key

    # WHEN
    # The handler processes the Kafka event with a null key
    result = handler(kafka_event_with_null_key, lambda_context)

    # THEN
    # The key should be preserved as None without any attempt at deserialization
    assert result is None


def test_kafka_consumer_json_with_wrong_avro_schema(kafka_event_with_json_data, lambda_context):
    # GIVEN
    # A Kafka event with a null key in the record
    kafka_event_wrong_metadata = deepcopy(kafka_event_with_json_data)
    kafka_event_wrong_metadata["records"]["my-topic-1"][0]["valueSchemaMetadata"] = {
        "dataFormat": "AVRO",
        "schemaId": "1234532323",
    }

    schema_config = SchemaConfig(value_schema_type="JSON")

    # A Kafka consumer with no schema configuration specified
    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Get the first record's key which should be None
        record = next(event.records)
        return record.value

    # WHEN
    # The handler processes the Kafka event with a null key
    with pytest.raises(KafkaConsumerDeserializationFormatMismatch) as excinfo:
        handler(kafka_event_wrong_metadata, lambda_context)

    # THEN
    # Ensure the error contains useful diagnostic information
    assert "Expected data is JSON but you sent " in str(excinfo.value)


def test_kafka_consumer_metadata_fields(kafka_event_with_json_data, lambda_context):
    # GIVEN
    # A Kafka event with specific metadata we want to verify is preserved
    kafka_event = deepcopy(kafka_event_with_json_data)
    kafka_event["records"]["my-topic-1"][0]["key"] = None

    # A Kafka consumer with no schema configuration
    # that returns the full record object for inspection
    @kafka_consumer()
    def handler(event: ConsumerRecords, context):
        return event.record

    # WHEN
    # The handler processes the Kafka event and returns the record object
    result = handler(kafka_event, lambda_context)

    # THEN
    # The record should preserve all original metadata fields

    # Original encoded values should be preserved
    assert result.original_value == kafka_event["records"]["my-topic-1"][0]["value"]
    assert result.original_key == kafka_event["records"]["my-topic-1"][0]["key"]

    # Original headers array should be preserved
    assert result.original_headers == kafka_event["records"]["my-topic-1"][0]["headers"]

    # Headers should be parsed into a dictionary for easy access
    assert result.headers == {"headerKey": b"headerValue"}

    # Additional metadata checks could be added here:
    assert result.topic == kafka_event["records"]["my-topic-1"][0]["topic"]
    assert result.partition == kafka_event["records"]["my-topic-1"][0]["partition"]
    assert result.offset == kafka_event["records"]["my-topic-1"][0]["offset"]
    assert result.timestamp == kafka_event["records"]["my-topic-1"][0]["timestamp"]
