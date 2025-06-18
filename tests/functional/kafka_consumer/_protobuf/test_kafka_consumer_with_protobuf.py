import base64
from copy import deepcopy
from dataclasses import dataclass

import pytest

from aws_lambda_powertools.utilities.kafka.consumer_records import ConsumerRecords
from aws_lambda_powertools.utilities.kafka.exceptions import (
    KafkaConsumerDeserializationError,
    KafkaConsumerMissingSchemaError,
)
from aws_lambda_powertools.utilities.kafka.kafka_consumer import kafka_consumer
from aws_lambda_powertools.utilities.kafka.schema_config import SchemaConfig

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


def test_kafka_consumer_with_protobuf(kafka_event_with_proto_data, lambda_context):
    # GIVEN A Kafka consumer configured to deserialize Protobuf data
    # using the User protobuf message type as the schema
    schema_config = SchemaConfig(
        value_schema_type="PROTOBUF",
        value_schema=User,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Return the deserialized record value for verification
        return event.record.value

    # WHEN The handler processes a Kafka event containing Protobuf-encoded data
    result = handler(kafka_event_with_proto_data, lambda_context)

    # THEN The Protobuf data should be correctly deserialized into a dictionary
    # with the expected field values from the User message
    assert result["name"] == "John Doe"
    assert result["age"] == 30


def test_kafka_consumer_with_proto_and_dataclass(
    kafka_event_with_proto_data,
    lambda_context,
):
    # GIVEN A Kafka consumer configured to deserialize Protobuf data
    # using the User message type as the schema and convert the result to a UserValueDataClass instance
    schema_config = SchemaConfig(
        value_schema_type="PROTOBUF",
        value_schema=User,
        value_output_serializer=UserValueDataClass,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Extract the deserialized and serialized value
        # which should be a UserValueDataClass instance
        value: UserValueDataClass = event.record.value
        return value

    # WHEN The handler processes a Kafka event containing Protobuf-encoded data
    # which is deserialized and then serialized to a dataclass
    result = handler(kafka_event_with_proto_data, lambda_context)

    # THEN The result should be a UserValueDataClass instance
    # with the correct property values from the original Protobuf message
    assert isinstance(result, UserValueDataClass)
    assert result.name == "John Doe"
    assert result.age == 30


def test_kafka_consumer_with_invalid_proto_data(kafka_event_with_proto_data, lambda_context):
    """Test error handling when Protobuf data is invalid."""
    # GIVEN A Kafka event with deliberately corrupted Protobuf data
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
        return record.value

    # WHEN/THEN
    # The handler should fail to process the invalid Avro data
    # and raise a specific deserialization error
    with pytest.raises(KafkaConsumerDeserializationError) as excinfo:
        lambda_handler(kafka_event_with_proto_data_temp, lambda_context)

    # The exact error message may vary depending on the Protobuf library's internals,
    # but should indicate a deserialization problem
    assert "Error trying to deserialize protobuf data" in str(excinfo.value)


def test_kafka_consumer_with_key_deserialization(
    kafka_event_with_proto_data,
    lambda_context,
):
    # GIVEN A Kafka consumer configured to deserialize only the key using Protobuf
    # and serialize it to a UserKeyClass instance
    schema_config = SchemaConfig(
        key_schema_type="PROTOBUF",
        key_schema=Key,
        key_output_serializer=UserKeyClass,
    )

    @kafka_consumer(schema_config=schema_config)
    def lambda_handler(event: ConsumerRecords, context):
        key: UserKeyClass = event.record.key
        return key

    # WHEN The handler processes a Kafka event, deserializing only the key portion
    # while leaving the value in its original format
    result = lambda_handler(kafka_event_with_proto_data, lambda_context)

    # THEN The key should be properly deserialized from Protobuf and serialized to a UserKeyClass
    # with the expected user_id value
    assert result.user_id == "user-123"
    assert isinstance(result, UserKeyClass)


def test_kafka_consumer_with_wrong_proto_message_class(kafka_event_with_proto_data, lambda_context):
    # GIVEN
    # A Kafka consumer configured with the wrong Protobuf message class (Key instead of User)
    # for deserializing the value payload
    schema_config = SchemaConfig(
        value_schema_type="PROTOBUF",
        value_schema=Key,  # Incorrect schema for the value data
    )

    @kafka_consumer(schema_config=schema_config)
    def lambda_handler(event: ConsumerRecords, context):
        record = next(event.records)
        return record.value

    # WHEN The handler processes a Kafka event with Protobuf data that doesn't match the schema
    response = lambda_handler(kafka_event_with_proto_data, lambda_context)

    # THEN The deserialization should return an empty result
    assert not response


def test_kafka_consumer_with_custom_function(
    kafka_event_with_proto_data,
    lambda_context,
):
    # GIVEN A custom serialization function that removes the age field from the dictionary
    def dict_output(data: dict) -> dict:
        # removing age key
        del data["age"]
        return data

    # A Kafka consumer configured with Protobuf schema deserialization
    # and a custom function for output transformation
    schema_config = SchemaConfig(
        value_schema_type="PROTOBUF",
        value_schema=User,
        value_output_serializer=dict_output,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        return event.record.value

    # WHEN The handler processes the Kafka event containing Protobuf-encoded data
    # and applies the custom transformation function to the output
    result = handler(kafka_event_with_proto_data, lambda_context)

    # THEN The Avro data should be correctly deserialized and transformed
    # with the name field intact but the age field removed
    assert result["name"] == "John Doe"
    assert "age" not in result


def test_kafka_consumer_with_multiple_records(lambda_context):
    """Test Kafka consumer with multiple records."""

    # GIVEN
    # Two distinct Protobuf User messages to create multiple records
    # First user: John Doe, age 30
    user1 = User()
    user1.name = "John Doe"
    user1.age = 30
    value1 = base64.b64encode(user1.SerializeToString()).decode("utf-8")

    # Second user: Jane Smith, age 25
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

    # WHEN
    # The handler processes the Kafka event containing multiple records
    result = handler(event, lambda_context)

    # THEN
    # The handler should successfully process both records
    # and return the correct count
    assert result == {"processed": 2}

    # All records should be correctly deserialized with proper values
    assert len(processed_records) == 2

    # First record should contain John Doe's details
    assert processed_records[0]["name"] == "John Doe"
    assert processed_records[0]["age"] == 30

    # Second record should contain Jane Smith's details
    assert processed_records[1]["name"] == "Jane Smith"
    assert processed_records[1]["age"] == 25


def test_kafka_consumer_without_protobuf_value_schema():
    # GIVEN
    # A scenario where PROTOBUF schema type is specified for the value
    # but no actual schema class is provided

    # WHEN/THEN
    # SchemaConfig initialization should fail with an appropriate error
    with pytest.raises(KafkaConsumerMissingSchemaError) as excinfo:
        SchemaConfig(value_schema_type="PROTOBUF", value_schema=None)

    # Verify the error message mentions the missing value schema
    assert "value_schema" in str(excinfo.value)
    assert "PROTOBUF" in str(excinfo.value)


def test_kafka_consumer_without_protobuf_key_schema():
    # GIVEN
    # A scenario where PROTOBUF schema type is specified for the key
    # but no actual schema class is provided

    # WHEN/THEN
    # SchemaConfig initialization should fail with an appropriate error
    with pytest.raises(KafkaConsumerMissingSchemaError) as excinfo:
        SchemaConfig(key_schema_type="PROTOBUF", key_schema=None)

    # Verify the error message mentions the missing key schema
    assert "key_schema" in str(excinfo.value)
    assert "PROTOBUF" in str(excinfo.value)
