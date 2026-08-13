import base64
import io
from copy import deepcopy
from dataclasses import dataclass

import pytest
from avro.io import BinaryEncoder, DatumWriter
from avro.schema import parse as parse_schema

from aws_lambda_powertools.utilities.kafka.consumer_records import ConsumerRecords
from aws_lambda_powertools.utilities.kafka.exceptions import (
    KafkaConsumerAvroSchemaParserError,
    KafkaConsumerDeserializationError,
    KafkaConsumerDeserializationFormatMismatch,
    KafkaConsumerMissingSchemaError,
)
from aws_lambda_powertools.utilities.kafka.kafka_consumer import kafka_consumer
from aws_lambda_powertools.utilities.kafka.schema_config import SchemaConfig


@pytest.fixture
def avro_value_schema():
    return """
    {
        "type": "record",
        "name": "User",
        "namespace": "com.example",
        "fields": [
            {"name": "name", "type": "string"},
            {"name": "age", "type": "int"}
        ]
    }
    """


@pytest.fixture
def avro_key_schema():
    return """
    {
        "type": "record",
        "name": "Key",
        "namespace": "com.example",
        "fields": [
            {"name": "user_id", "type": "string"}
        ]
    }
    """


@pytest.fixture
def avro_encoded_value(avro_value_schema):
    parsed_schema = parse_schema(avro_value_schema)
    writer = DatumWriter(parsed_schema)
    bytes_writer = io.BytesIO()
    encoder = BinaryEncoder(bytes_writer)
    writer.write({"name": "John Doe", "age": 30}, encoder)
    return base64.b64encode(bytes_writer.getvalue()).decode("utf-8")


@pytest.fixture
def avro_encoded_key(avro_key_schema):
    parsed_key_schema = parse_schema(avro_key_schema)
    writer = DatumWriter(parsed_key_schema)
    bytes_writer = io.BytesIO()
    encoder = BinaryEncoder(bytes_writer)
    writer.write({"user_id": "user-123"}, encoder)
    return base64.b64encode(bytes_writer.getvalue()).decode("utf-8")


SCHEMA_ID_PREFIX = b"\x00\x00\x00\x00\x01"


def _prepend_prefix_to_base64(encoded: str, prefix: bytes = SCHEMA_ID_PREFIX) -> str:
    return base64.b64encode(prefix + base64.b64decode(encoded)).decode("utf-8")


@pytest.fixture
def avro_encoded_value_with_prefix(avro_encoded_value):
    return _prepend_prefix_to_base64(avro_encoded_value)


@pytest.fixture
def avro_encoded_key_with_prefix(avro_encoded_key):
    return _prepend_prefix_to_base64(avro_encoded_key)


@pytest.fixture
def kafka_event_with_avro_data(avro_encoded_value, avro_encoded_key):
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
                    "key": avro_encoded_key,
                    "value": avro_encoded_value,
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


def test_kafka_consumer_with_avro(kafka_event_with_avro_data, avro_value_schema, lambda_context):
    # GIVEN A Kafka consumer configured with Avro schema deserialization
    schema_config = SchemaConfig(value_schema_type="AVRO", value_schema=avro_value_schema)

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        return event.record.value

    # WHEN The handler processes the Kafka event containing Avro-encoded data
    result = handler(kafka_event_with_avro_data, lambda_context)

    # THEN The Avro data should be correctly deserialized into a Python dictionary
    assert result["name"] == "John Doe"
    assert result["age"] == 30


def test_kafka_consumer_with_avro_and_dataclass(
    kafka_event_with_avro_data,
    avro_value_schema,
    lambda_context,
):
    # GIVEN A Kafka consumer configured with Avro schema deserialization
    # and a dataclass for output serialization
    schema_config = SchemaConfig(
        value_schema_type="AVRO",
        value_schema=avro_value_schema,
        value_output_serializer=UserValueDataClass,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        value: UserValueDataClass = event.record.value
        return value

    # WHEN The handler processes the Kafka event containing Avro-encoded data
    # and serializes the output as a UserValueDataClass instance
    result = handler(kafka_event_with_avro_data, lambda_context)

    # THEN The Avro data should be correctly deserialized and converted to a dataclass instance
    # with the expected property values
    assert result.name == "John Doe"
    assert result.age == 30
    assert isinstance(result, UserValueDataClass)


def test_kafka_consumer_with_avro_and_custom_function(
    kafka_event_with_avro_data,
    avro_value_schema,
    lambda_context,
):
    # GIVEN A custom serialization function that removes the age field from the dictionary
    def dict_output(data: dict) -> dict:
        # removing age key
        del data["age"]
        return data

    # A Kafka consumer configured with Avro schema deserialization
    # and a custom function for output transformation
    schema_config = SchemaConfig(
        value_schema_type="AVRO",
        value_schema=avro_value_schema,
        value_output_serializer=dict_output,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        return event.record.value

    # WHEN The handler processes the Kafka event containing Avro-encoded data
    # and applies the custom transformation function to the output
    result = handler(kafka_event_with_avro_data, lambda_context)

    # THEN The Avro data should be correctly deserialized and transformed
    # with the name field intact but the age field removed
    assert result["name"] == "John Doe"
    assert "age" not in result


def test_kafka_consumer_with_invalid_avro_data(kafka_event_with_avro_data, lambda_context, avro_value_schema):
    # GIVEN A Kafka event with deliberately corrupted Avro data
    invalid_data = base64.b64encode(b"invalid avro data").decode("utf-8")
    kafka_event_with_avro_data_temp = deepcopy(kafka_event_with_avro_data)
    kafka_event_with_avro_data_temp["records"]["my-topic-1"][0]["value"] = invalid_data

    schema_config = SchemaConfig(value_schema_type="AVRO", value_schema=avro_value_schema)

    @kafka_consumer(schema_config=schema_config)
    def lambda_handler(event: ConsumerRecords, context):
        # This should never be reached if deserializer fails
        return event.record.value

    # WHEN/THEN
    # The handler should fail to process the invalid Avro data
    # and raise a specific deserialization error
    with pytest.raises(KafkaConsumerDeserializationError) as excinfo:
        lambda_handler(kafka_event_with_avro_data_temp, lambda_context)

    # The exact error message may vary depending on the Avro library's internals,
    # but should indicate a deserialization problem
    assert "Error trying to deserialize avro data" in str(excinfo.value)


def test_kafka_consumer_with_invalid_avro_schema(kafka_event_with_avro_data, lambda_context):
    # GIVEN
    # An intentionally malformed Avro schema with syntax errors
    avro_schema = """
    {
        "type": "record",
        "name": "User",
        "namespace": "com.example",
        "fields": [ "invalid schema" ]
    }
    """

    # A Kafka consumer configured with the invalid schema
    schema_config = SchemaConfig(value_schema_type="AVRO", value_schema=avro_schema)

    @kafka_consumer(schema_config=schema_config)
    def lambda_handler(event: ConsumerRecords, context):
        # This should never be reached if deserializer fails
        return event.record.value

    # WHEN/THEN
    # The handler should fail during initialization when it tries to parse the schema
    # and raise a specific schema parser error
    with pytest.raises(KafkaConsumerAvroSchemaParserError) as excinfo:
        lambda_handler(kafka_event_with_avro_data, lambda_context)

    # The exact error message may vary depending on the Avro library's internals,
    # but should indicate a deserialization problem
    assert "Invalid Avro schema. Please ensure the provided avro schema is valid:" in str(excinfo.value)


def test_kafka_consumer_with_key_deserialization(
    kafka_event_with_avro_data,
    lambda_context,
    avro_value_schema,
    avro_key_schema,
):
    """Test deserializing both key and value with different schemas and serializers."""

    key_value_result = {}

    # GIVEN A Kafka consumer configured with Avro schemas for both key and value
    # with different output serializers for each
    schema_config = SchemaConfig(
        value_schema_type="AVRO",
        value_schema=avro_value_schema,
        value_output_serializer=UserValueDataClass,
        key_schema_type="AVRO",
        key_schema=avro_key_schema,
        key_output_serializer=UserKeyClass,
    )

    @kafka_consumer(schema_config=schema_config)
    def lambda_handler(event: ConsumerRecords, context):
        record = next(event.records)
        key_value_result["key_type"] = type(record.key).__name__
        key_value_result["key_id"] = record.key.user_id
        key_value_result["value_type"] = type(record.value).__name__
        key_value_result["value_name"] = record.value.name
        key_value_result["value_age"] = record.value.age
        return {"processed": True}

    # WHEN
    # The handler processes the Kafka event, deserializing both key and value
    result = lambda_handler(kafka_event_with_avro_data, lambda_context)

    # THEN
    # The handler should return success and the captured properties should match expectations
    assert result == {"processed": True}

    # Key should be correctly deserialized into a UserKeyClass instance
    assert key_value_result["key_type"] == "UserKeyClass"
    assert key_value_result["key_id"] == "user-123"

    # Value should be correctly deserialized into a UserValueDataClass instance
    assert key_value_result["value_type"] == "UserValueDataClass"
    assert key_value_result["value_name"] == "John Doe"
    assert key_value_result["value_age"] == 30


def test_kafka_consumer_without_avro_value_schema():
    # GIVEN
    # A scenario where AVRO schema type is specified for value
    # but no actual schema is provided

    # WHEN/THEN
    # SchemaConfig initialization should fail with an appropriate error
    with pytest.raises(KafkaConsumerMissingSchemaError) as excinfo:
        SchemaConfig(value_schema_type="AVRO", value_schema=None)

    # Verify the error message mentions 'value_schema'
    assert "value_schema" in str(excinfo.value)


def test_kafka_consumer_without_avro_key_schema():
    # GIVEN
    # A scenario where AVRO schema type is specified for key
    # but no actual schema is provided

    # WHEN/THEN
    # SchemaConfig initialization should fail with an appropriate error
    with pytest.raises(KafkaConsumerMissingSchemaError) as excinfo:
        SchemaConfig(key_schema_type="AVRO", key_schema=None)

    # Verify the error message mentions 'key_schema'
    assert "key_schema" in str(excinfo.value)


def test_kafka_consumer_avro_produces_wrong_output_without_prefix_length_setting(
    kafka_event_with_avro_data,
    avro_encoded_value_with_prefix,
    avro_value_schema,
    lambda_context,
):
    # GIVEN An Avro payload that has been serialized by a Confluent-style producer,
    # so it carries a 5-byte "magic byte + schema ID" prefix in front of the Avro body
    event = deepcopy(kafka_event_with_avro_data)
    event["records"]["my-topic-1"][0]["value"] = avro_encoded_value_with_prefix

    # AND a SchemaConfig without the new offset parameter (today's behaviour)
    schema_config = SchemaConfig(value_schema_type="AVRO", value_schema=avro_value_schema)

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        return event.record.value

    # WHEN/THEN The deserializer cannot know it should skip the leading bytes.
    # Depending on the prefix content, this either raises or silently returns corrupted data.
    # Both outcomes are broken; the fix must let callers opt into skipping the prefix.
    try:
        result = handler(event, lambda_context)
    except KafkaConsumerDeserializationError:
        return

    assert result != {"name": "John Doe", "age": 30}


def test_kafka_consumer_avro_with_value_schema_id_prefix_length(
    kafka_event_with_avro_data,
    avro_encoded_value_with_prefix,
    avro_value_schema,
    lambda_context,
):
    # GIVEN An Avro payload with a 5-byte magic-byte + schema-ID prefix
    event = deepcopy(kafka_event_with_avro_data)
    event["records"]["my-topic-1"][0]["value"] = avro_encoded_value_with_prefix

    # AND a SchemaConfig instructed to skip the first 5 bytes before Avro decoding
    schema_config = SchemaConfig(
        value_schema_type="AVRO",
        value_schema=avro_value_schema,
        value_schema_id_prefix_length=5,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        return event.record.value

    # WHEN The handler processes the event
    result = handler(event, lambda_context)

    # THEN The Avro body should be decoded correctly after the prefix is stripped
    assert result["name"] == "John Doe"
    assert result["age"] == 30


def test_kafka_consumer_avro_with_key_schema_id_prefix_length(
    kafka_event_with_avro_data,
    avro_encoded_key_with_prefix,
    avro_value_schema,
    avro_key_schema,
    lambda_context,
):
    # GIVEN A Kafka event whose key is Avro data behind a 5-byte prefix
    event = deepcopy(kafka_event_with_avro_data)
    event["records"]["my-topic-1"][0]["key"] = avro_encoded_key_with_prefix

    # AND a SchemaConfig that only strips the prefix on the key side
    schema_config = SchemaConfig(
        value_schema_type="AVRO",
        value_schema=avro_value_schema,
        key_schema_type="AVRO",
        key_schema=avro_key_schema,
        key_schema_id_prefix_length=5,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        record = next(event.records)
        return {"key": record.key, "value": record.value}

    # WHEN The handler processes the event
    result = handler(event, lambda_context)

    # THEN Both key (prefixed, offset applied) and value (plain) deserialize correctly
    assert result["key"] == {"user_id": "user-123"}
    assert result["value"] == {"name": "John Doe", "age": 30}


def test_kafka_consumer_avro_with_wrong_json_schema(
    kafka_event_with_avro_data,
    lambda_context,
    avro_value_schema,
    avro_key_schema,
):
    # GIVEN
    # A Kafka event with a null key in the record
    kafka_event_wrong_metadata = deepcopy(kafka_event_with_avro_data)
    kafka_event_wrong_metadata["records"]["my-topic-1"][0]["valueSchemaMetadata"] = {
        "dataFormat": "JSON",
        "schemaId": "123",
    }

    schema_config = SchemaConfig(value_schema_type="AVRO", value_schema=avro_value_schema)

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
    assert "Expected data is AVRO but you sent " in str(excinfo.value)
