import base64
from copy import deepcopy
from dataclasses import dataclass

import pytest

from aws_lambda_powertools.utilities.kafka_consumer.consumer_records import ConsumerRecords
from aws_lambda_powertools.utilities.kafka_consumer.exceptions import (
    KafkaConsumerDeserializationError,
    KafkaConsumerMissingSchemaError,
)
from aws_lambda_powertools.utilities.kafka_consumer.kafka_consumer import kafka_consumer
from aws_lambda_powertools.utilities.kafka_consumer.schema_config import SchemaConfig

# Import the generated protobuf classes
from .user_pb2 import Key, User


@pytest.fixture
def proto_encoded_value():
    # Create a User protobuf message
    user = User()
    user.name = "John Doe"
    user.age = 30
    # Serialize and encode in base64
    return base64.b64encode(user.SerializeToString()).decode("utf-8")


@pytest.fixture
def proto_encoded_key():
    # Create a Key protobuf message
    key = Key()
    key.user_id = "user-123"
    # Serialize and encode in base64
    return base64.b64encode(key.SerializeToString()).decode("utf-8")


@pytest.fixture
def kafka_event_with_proto_data(proto_encoded_value, proto_encoded_key):
    return {
        "eventSource": "aws:kafka",
        "eventSourceArn": "arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster/abcdefg",
        "records": {
            "my-topic-1": [
                {
                    "topic": "my-topic-1",
                    "partition": 1,
                    "offset": 15,
                    "timestamp": 1545084650987,
                    "timestampType": "CREATE_TIME",
                    "key": proto_encoded_key,
                    "value": proto_encoded_value,
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


def test_kafka_consumer_with_proto(kafka_event_with_proto_data, lambda_context):
    """Test Kafka consumer with Protobuf deserialization without output serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(
        value_schema_type="PROTOBUF",
        value_schema=User,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        record = next(event.records)
        result_data["value_type"] = type(record.value).__name__
        result_data["name"] = record.value["name"]
        result_data["age"] = record.value["age"]
        return {"processed": True}

    # Call the handler
    result = handler(kafka_event_with_proto_data, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert result_data["value_type"] == "dict"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_proto_and_dataclass(
    kafka_event_with_proto_data,
    lambda_context,
):
    """Test Kafka consumer with Protobuf deserialization and dataclass output serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(
        value_schema_type="PROTOBUF",
        value_schema=User,
        value_output_serializer=UserValueDataClass,
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
    result = handler(kafka_event_with_proto_data, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert result_data["value_type"] == "UserValueDataClass"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_invalid_proto_data(kafka_event_with_proto_data, lambda_context):
    """Test error handling when Protobuf data is invalid."""
    # Create invalid protobuf data
    invalid_data = base64.b64encode(b"invalid protobuf data").decode("utf-8")
    kafka_event_with_proto_data_temp = deepcopy(kafka_event_with_proto_data)
    kafka_event_with_proto_data_temp["records"]["my-topic-1"][0]["value"] = invalid_data

    schema_config = SchemaConfig(
        value_schema_type="PROTOBUF",
        value_schema=User,
    )

    @kafka_consumer(schema_config=schema_config)
    def lambda_handler(event: ConsumerRecords, context):
        # This should never be reached if deserializer fails
        record = next(event.records)
        assert record.value
        return {"processed": True}

    # This should raise a deserialization error
    with pytest.raises(KafkaConsumerDeserializationError) as excinfo:
        lambda_handler(kafka_event_with_proto_data_temp, lambda_context)

    # The error message should indicate a deserialization problem
    assert "Error trying to deserialize protobuf data" in str(excinfo.value)


def test_kafka_consumer_with_key_deserialization(
    kafka_event_with_proto_data,
    lambda_context,
):
    """Test deserializing both key and value with different schemas and serializers."""

    # Create dict to capture results
    key_value_result = {}

    # Create schema config with both key and value
    schema_config = SchemaConfig(
        key_schema_type="PROTOBUF",
        key_schema=Key,
        key_output_serializer=UserKeyClass,
    )

    @kafka_consumer(schema_config=schema_config)
    def lambda_handler(event: ConsumerRecords, context):
        record = next(event.records)
        key_value_result["key_type"] = type(record.key).__name__
        key_value_result["key_id"] = record.key.user_id
        return {"processed": True}

    # Call the handler
    result = lambda_handler(kafka_event_with_proto_data, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert key_value_result["key_type"] == "UserKeyClass"
    assert key_value_result["key_id"] == "user-123"


def test_kafka_consumer_with_wrong_proto_message_class(kafka_event_with_proto_data, lambda_context):
    """Test error handling when wrong proto message class is provided."""

    schema_config = SchemaConfig(
        value_schema_type="PROTOBUF",
        value_schema=Key,
    )

    @kafka_consumer(schema_config=schema_config)
    def lambda_handler(event: ConsumerRecords, context):
        record = next(event.records)
        return record.value

    # This should raise a deserialization error
    response = lambda_handler(kafka_event_with_proto_data, lambda_context)

    assert not response


def test_kafka_consumer_with_custom_object(
    kafka_event_with_proto_data,
    lambda_context,
):
    """Test Kafka consumer with Protobuf deserialization and custom object serialization."""

    # Define a custom output object class
    class UserCustomObject:
        def __init__(self, proto_message):
            self.name = proto_message.name
            self.age = proto_message.age
            self.custom_field = f"{proto_message.name} is {proto_message.age} years old"

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(
        value_schema_type="PROTOBUF",
        value_schema=User,
        value_output_serializer=lambda msg: UserCustomObject(msg),
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        record = next(event.records)
        result_data["value_type"] = type(record.value).__name__
        result_data["name"] = record.value.name
        result_data["age"] = record.value.age
        result_data["custom_field"] = record.value.custom_field
        return {"processed": True}

    # Call the handler
    result = handler(kafka_event_with_proto_data, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert result_data["value_type"] == "UserCustomObject"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30
    assert result_data["custom_field"] == "John Doe is 30 years old"


def test_kafka_consumer_with_multiple_records(lambda_context):
    """Test Kafka consumer with multiple records."""

    # Create first user
    user1 = User()
    user1.name = "John Doe"
    user1.age = 30
    value1 = base64.b64encode(user1.SerializeToString()).decode("utf-8")

    # Create second user
    user2 = User()
    user2.name = "Jane Smith"
    user2.age = 25
    value2 = base64.b64encode(user2.SerializeToString()).decode("utf-8")

    # Create event with multiple records
    event = {
        "eventSource": "aws:kafka",
        "records": {
            "my-topic-1": [
                {
                    "topic": "my-topic-1",
                    "partition": 0,
                    "offset": 15,
                    "timestamp": 1545084650987,
                    "timestampType": "CREATE_TIME",
                    "value": value1,
                },
                {
                    "topic": "my-topic-1",
                    "partition": 0,
                    "offset": 16,
                    "timestamp": 1545084651000,
                    "timestampType": "CREATE_TIME",
                    "value": value2,
                },
            ],
        },
    }

    # Create dict to capture results
    processed_records = []

    schema_config = SchemaConfig(
        value_schema_type="PROTOBUF",
        value_schema=User,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        for record in event.records:
            processed_records.append({"name": record.value["name"], "age": record.value["age"]})
        return {"processed": len(processed_records)}

    # Call the handler
    result = handler(event, lambda_context)

    # Verify the results
    assert result == {"processed": 2}
    assert len(processed_records) == 2
    assert processed_records[0]["name"] == "John Doe"
    assert processed_records[0]["age"] == 30
    assert processed_records[1]["name"] == "Jane Smith"
    assert processed_records[1]["age"] == 25


def test_kafka_consumer_without_protobuf_value_schema():
    """Test error handling when Avro data is invalid."""

    with pytest.raises(KafkaConsumerMissingSchemaError):
        SchemaConfig(value_schema_type="PROTOBUF", value_schema=None)


def test_kafka_consumer_without_protobuf_key_schema():
    """Test error handling when Avro data is invalid."""

    with pytest.raises(KafkaConsumerMissingSchemaError):
        SchemaConfig(key_schema_type="PROTOBUF", key_schema=None)
