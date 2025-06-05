import base64
import io
from copy import deepcopy

import pytest
from avro.io import BinaryEncoder, DatumWriter
from avro.schema import parse as parse_schema

from aws_lambda_powertools.utilities.kafka_consumer.consumer_records import ConsumerRecords
from aws_lambda_powertools.utilities.kafka_consumer.exceptions import (
    KafkaConsumerAvroSchemaParserError,
    KafkaConsumerDeserializationError,
)
from aws_lambda_powertools.utilities.kafka_consumer.kafka_consumer import kafka_consumer
from aws_lambda_powertools.utilities.kafka_consumer.schema_config import SchemaConfig


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


def test_kafka_consumer_with_avro_and_dataclass(
    kafka_event_with_avro_data, avro_value_schema, lambda_context, user_value_dataclass,
):
    """Test Kafka consumer with Avro deserialization and dataclass output serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(
        value_schema_type="AVRO",
        value_schema=avro_value_schema,
        value_output_serializer=user_value_dataclass,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        record = next(event.records)
        result_data["value_type"] = type(record.value).__name__
        result_data["name"] = record.value.name
        result_data["age"] = record.value.age
        return {"processed": True}

    # Call the handler
    result = handler(kafka_event_with_avro_data, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert result_data["value_type"] == "UserValueDataClass"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_avro_and_custom_object(
    kafka_event_with_avro_data, avro_value_schema, lambda_context, user_value_dict,
):
    """Test Kafka consumer with Avro deserialization and custom object serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(
        value_schema_type="AVRO",
        value_schema=avro_value_schema,
        value_output_serializer=user_value_dict,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        record = next(event.records)
        result_data["value_type"] = type(record.value).__name__
        result_data["name"] = record.value.name
        result_data["age"] = record.value.age
        return {"processed": True}

    # Call the handler
    result = handler(kafka_event_with_avro_data, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert result_data["value_type"] == "UserValueDict"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_avro_raw(kafka_event_with_avro_data, avro_value_schema, lambda_context):
    """Test Kafka consumer with Avro deserialization without output serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(value_schema_type="AVRO", value_schema=avro_value_schema)

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        record = next(event.records)
        result_data["value_type"] = type(record.value).__name__
        result_data["name"] = record.value["name"]
        result_data["age"] = record.value["age"]
        return {"processed": True}

    # Call the handler
    result = handler(kafka_event_with_avro_data, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert result_data["value_type"] == "dict"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_invalid_avro_data(kafka_event_with_avro_data, lambda_context, avro_value_schema):
    """Test error handling when Avro data is invalid."""
    # Create invalid avro data
    invalid_data = base64.b64encode(b"invalid avro data").decode("utf-8")
    kafka_event_with_avro_data_temp = deepcopy(kafka_event_with_avro_data)
    kafka_event_with_avro_data_temp["records"]["my-topic-1"][0]["value"] = invalid_data

    schema_config = SchemaConfig(value_schema_type="AVRO", value_schema=avro_value_schema)

    @kafka_consumer(schema_config=schema_config)
    def lambda_handler(event: ConsumerRecords, context):
        # This should never be reached if deserializer fails
        record = next(event.records)
        assert record.value
        return {"processed": True}

    # This should raise a deserialization error
    with pytest.raises(KafkaConsumerDeserializationError) as excinfo:
        lambda_handler(kafka_event_with_avro_data_temp, lambda_context)

    # The exact error message may vary depending on the Avro library's internals,
    # but should indicate a deserialization problem
    assert "Error trying to deserializer avro data" in str(excinfo.value)


def test_kafka_consumer_with_invalid_avro_schema(kafka_event_with_avro_data, lambda_context):
    """Test error handling when Avro data is invalid."""

    avro_schema = """
    {
        "type": "record",
        "name": "User",
        "namespace": "com.example",
        "fields": [ "invalid schema" ]
    }
    """

    schema_config = SchemaConfig(value_schema_type="AVRO", value_schema=avro_schema)

    @kafka_consumer(schema_config=schema_config)
    def lambda_handler(event: ConsumerRecords, context):
        # This should never be reached if deserializer fails
        record = next(event.records)
        assert record.value
        return {"processed": True}

    # This should raise a deserialization error
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
    user_value_dataclass,
    user_key_dataclass,
):
    """Test deserializing both key and value with different schemas and serializers."""

    # Create dict to capture results
    key_value_result = {}

    # Create schema config with both key and value
    schema_config = SchemaConfig(
        value_schema_type="AVRO",
        value_schema=avro_value_schema,
        value_output_serializer=user_value_dataclass,
        key_schema_type="AVRO",
        key_schema=avro_key_schema,
        key_output_serializer=user_key_dataclass,
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

    # Call the handler
    result = lambda_handler(kafka_event_with_avro_data, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert key_value_result["key_type"] == "UserKeyClass"
    assert key_value_result["key_id"] == "user-123"
    assert key_value_result["value_type"] == "UserValueDataClass"
    assert key_value_result["value_name"] == "John Doe"
    assert key_value_result["value_age"] == 30


def test_kafka_consumer_with_different_serializers_for_key_and_value(
    kafka_event_with_avro_data, lambda_context, avro_value_schema, avro_key_schema, user_key_dataclass, user_value_dict,
):
    """Test using different serializer types for key and value."""

    # Create dict to capture results
    results = {}

    # Create schema config with different serializers
    schema_config = SchemaConfig(
        value_schema_type="AVRO",
        value_schema=avro_value_schema,
        value_output_serializer=user_value_dict,
        key_schema_type="AVRO",
        key_schema=avro_key_schema,
        key_output_serializer=user_key_dataclass,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        record = next(event.records)
        results["key_type"] = type(record.key).__name__
        results["key_id"] = record.key.user_id
        results["value_type"] = type(record.value).__name__
        results["value_name"] = record.value.name
        results["value_age"] = record.value.age
        return {"processed": True}

    # Call the handler
    result = handler(kafka_event_with_avro_data, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert results["key_type"] == "UserKeyClass"
    assert results["key_id"] == "user-123"
    assert results["value_type"] == "UserValueDict"
    assert results["value_name"] == "John Doe"
    assert results["value_age"] == 30
