import base64
import json
from typing import Annotated, Literal

import pytest
from pydantic import BaseModel, Field

from aws_lambda_powertools.utilities.kafka.consumer_records import ConsumerRecords
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


class UserValueModel(BaseModel):
    name: str
    age: int


class UserKeyModel(BaseModel):
    user_id: str


def test_kafka_consumer_with_json_value_and_pydantic(kafka_event_with_json_data, lambda_context):
    # GIVEN
    # A Kafka consumer configured to deserialize JSON data
    # and convert it to a Pydantic model instance
    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=UserValueModel)

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Extract the deserialized and serialized value
        # which should be a UserValueModel instance
        value: UserValueModel = event.record.value
        return value

    # WHEN
    # The handler processes a Kafka event containing JSON-encoded data
    # which is deserialized into a dictionary and then converted to a Pydantic model
    result = handler(kafka_event_with_json_data, lambda_context)

    # THEN
    # The result should be a UserValueModel instance with the correct properties
    assert isinstance(result, UserValueModel)
    assert result.name == "John Doe"
    assert result.age == 30


def test_kafka_consumer_with_json_value_and_union_tag(kafka_event_with_json_data, lambda_context):
    """Test Kafka consumer with JSON deserialization and dataclass output serialization."""

    class UserValueModel(BaseModel):
        name: Literal["John Doe"]
        age: int

    class UserValueModel2(BaseModel):
        name: Literal["Not using"]
        email: str

    UnionModel = Annotated[UserValueModel | UserValueModel2, Field(discriminator="name")]

    # GIVEN
    # A Kafka consumer configured to deserialize JSON data
    # and convert it to a Pydantic model instance with Union Tags
    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=UnionModel)

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Extract the deserialized and serialized value
        # which should be a UserValueModel instance
        value: UserValueModel = event.record.value
        return value

    # WHEN
    # The handler processes a Kafka event containing JSON-encoded data
    # which is deserialized into a dictionary and then converted to a Pydantic model
    result = handler(kafka_event_with_json_data, lambda_context)

    # THEN
    # The result should be a UserValueModel instance with the correct properties
    assert isinstance(result, UserValueModel)
    assert result.name == "John Doe"
    assert result.age == 30


def test_kafka_consumer_with_json_key_and_pydantic(kafka_event_with_json_data, lambda_context):
    # GIVEN
    # A Kafka consumer configured to deserialize only the key using JSON
    # and convert it to a Pydantic UserKeyModel instance
    schema_config = SchemaConfig(
        key_schema_type="JSON",
        key_output_serializer=UserKeyModel,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Extract the deserialized key to verify
        key: UserKeyModel = event.record.key
        return key

    # WHEN
    # The handler processes a Kafka event, deserializing only the key portion as JSON
    # while leaving the value in its original format
    result = handler(kafka_event_with_json_data, lambda_context)

    # THEN
    # The key should be properly deserialized from JSON and converted to a UserKeyModel
    # with the expected user_id value
    assert isinstance(result, UserKeyModel)
    assert result.user_id == "123"


def test_kafka_consumer_with_multiple_records(lambda_context):
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

    # A Kafka consumer configured to deserialize JSON and convert to Pydantic models
    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=UserValueModel)

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

    # All three users should be correctly deserialized and processed
    # regardless of their order in the event
    assert any(r["name"] == "John Doe" and r["age"] == 30 for r in processed_records)
    assert any(r["name"] == "Jane Smith" and r["age"] == 25 for r in processed_records)
    assert any(r["name"] == "Bob Johnson" and r["age"] == 40 for r in processed_records)
