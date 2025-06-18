import base64
import json
from typing import Literal, Union

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
    """Test Kafka consumer with JSON deserialization and dataclass output serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=UserValueModel)

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
    assert result_data["value_type"] == "UserValueModel"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_json_value_and_union_tag(kafka_event_with_json_data, lambda_context):
    """Test Kafka consumer with JSON deserialization and dataclass output serialization."""

    # Create dict to capture results
    result_data = {}

    class UserValueModel(BaseModel):
        name: Literal["John Doe"]
        age: int

    class UserValueModel2(BaseModel):
        name: Literal["Not using"]
        email: str

    class Model(BaseModel):
        name: Union[UserValueModel, UserValueModel2] = Field(discriminator="name")

    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=UserValueModel)

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
    assert result_data["value_type"] == "UserValueModel"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_json_key_and_pydantic(kafka_event_with_json_data, lambda_context):
    """Test Kafka consumer with JSON deserialization and dataclass output serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(key_schema_type="JSON", key_output_serializer=UserKeyModel)

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        record = next(event.records)
        result_data["value_type"] = type(record.key).__name__
        result_data["user_id"] = record.key.user_id
        return {"processed": True}

    # Call the handler
    result = handler(kafka_event_with_json_data, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert result_data["value_type"] == "UserKeyModel"
    assert result_data["user_id"] == "123"


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
    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=UserValueModel)

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
