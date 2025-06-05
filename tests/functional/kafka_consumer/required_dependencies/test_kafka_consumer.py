import base64
import io
import json
from dataclasses import dataclass

import pytest
from avro.io import BinaryEncoder, DatumWriter
from avro.schema import parse as parse_schema
from pydantic import BaseModel

from aws_lambda_powertools.utilities.kafka_consumer.consumer_records import ConsumerRecords
from aws_lambda_powertools.utilities.kafka_consumer.kafka_consumer import kafka_consumer
from aws_lambda_powertools.utilities.kafka_consumer.schema_config import SchemaConfig


class LambdaContext:
    def __init__(self):
        self.function_name = "test-func"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:eu-west-1:809313241234:function:test-func"
        self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    def get_remaining_time_in_millis(self) -> int:
        return 1000


@pytest.fixture
def lambda_context():
    return LambdaContext()


@pytest.fixture
def avro_schema():
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
def avro_encoded_data():
    schema_str = """
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
    parsed_schema = parse_schema(schema_str)
    writer = DatumWriter(parsed_schema)
    bytes_writer = io.BytesIO()
    encoder = BinaryEncoder(bytes_writer)
    writer.write({"name": "John Doe", "age": 30}, encoder)
    return base64.b64encode(bytes_writer.getvalue()).decode("utf-8")


@pytest.fixture
def json_encoded_data():
    data = {"name": "John Doe", "age": 30}
    return base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")


@pytest.fixture
def kafka_event_with_avro_data(avro_encoded_data):
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
                    "key": None,
                    "value": avro_encoded_data,
                    "headers": [{"headerKey": [104, 101, 97, 100, 101, 114, 86, 97, 108, 117, 101]}],
                },
            ],
        },
    }


@pytest.fixture
def kafka_event_with_json_data(json_encoded_data):
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
                    "key": None,
                    "value": json_encoded_data,
                    "headers": [{"headerKey": [104, 101, 97, 100, 101, 114, 86, 97, 108, 117, 101]}],
                },
            ],
        },
    }


# Test Models


class UserSchema(BaseModel):
    name: str
    age: int


@dataclass
class UserDataClass:
    name: str
    age: int


class UserDict:
    def __init__(self, name=None, age=None):
        self.name = name
        self.age = age

    @classmethod
    def from_dict(cls, data):
        return cls(name=data.get("name"), age=data.get("age"))

    def to_dict(self):
        return {"name": self.name, "age": self.age}


# Tests for Kafka Consumer with Avro Deserializer


def test_kafka_consumer_with_avro_and_pydantic(kafka_event_with_avro_data, avro_schema, lambda_context):
    """Test Kafka consumer with Avro deserialization and Pydantic output serialization."""

    # Create temp file to capture results
    result_data = {}

    schema_config = SchemaConfig(
        value_schema_type="AVRO",
        value_schema=avro_schema,
        value_output_serializer=UserSchema,
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
    assert result_data["value_type"] == "UserSchema"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_avro_and_dataclass(kafka_event_with_avro_data, avro_schema, lambda_context):
    """Test Kafka consumer with Avro deserialization and dataclass output serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(
        value_schema_type="AVRO",
        value_schema=avro_schema,
        value_output_serializer=UserDataClass,
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
    assert result_data["value_type"] == "UserDataClass"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_avro_and_custom_object(kafka_event_with_avro_data, avro_schema, lambda_context):
    """Test Kafka consumer with Avro deserialization and custom object serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(
        value_schema_type="AVRO",
        value_schema=avro_schema,
        value_output_serializer=UserDict,
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
    assert result_data["value_type"] == "UserDict"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_avro_raw(kafka_event_with_avro_data, avro_schema, lambda_context):
    """Test Kafka consumer with Avro deserialization without output serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(value_schema_type="AVRO", value_schema=avro_schema)

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


# Tests for Kafka Consumer with JSON Deserializer


def test_kafka_consumer_with_json_and_pydantic(kafka_event_with_json_data, lambda_context):
    """Test Kafka consumer with JSON deserialization and Pydantic output serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=UserSchema)

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
    assert result_data["value_type"] == "UserSchema"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_json_and_dataclass(kafka_event_with_json_data, lambda_context):
    """Test Kafka consumer with JSON deserialization and dataclass output serialization."""

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=UserDataClass)

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
    assert result_data["value_type"] == "UserDataClass"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30


def test_kafka_consumer_with_json_raw(kafka_event_with_json_data, lambda_context):
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


# Tests for Error Handling


def test_kafka_consumer_with_avro_missing_schema():
    """Test error handling when Avro schema is missing."""

    with pytest.raises(ValueError) as excinfo:
        # This will raise validation error in SchemaConfig init
        SchemaConfig(value_schema_type="AVRO", value_schema=None)

    assert "value_schema_str must be provided" in str(excinfo.value)


def test_kafka_consumer_with_invalid_avro_data(lambda_context):
    """Test error handling when Avro data is invalid."""

    avro_schema = """
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

    # Create invalid avro data
    invalid_data = base64.b64encode(b"invalid avro data").decode("utf-8")

    kafka_event = {
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
                    "value": invalid_data,
                    "headers": [],
                },
            ],
        },
    }

    schema_config = SchemaConfig(value_schema_type="AVRO", value_schema=avro_schema)

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # This should never be reached if deserializer fails
        return {"processed": True}

    # This should raise a deserialization error
    with pytest.raises(Exception) as excinfo:
        handler(kafka_event, lambda_context)

    # The exact error message may vary depending on the Avro library's internals,
    # but should indicate a deserialization problem
    assert "deseriali" in str(excinfo.value).lower() or "avro" in str(excinfo.value).lower()


def test_kafka_consumer_with_invalid_json_data(lambda_context):
    """Test error handling when JSON data is invalid."""

    # Create invalid JSON data
    invalid_data = base64.b64encode(b"invalid json data").decode("utf-8")

    kafka_event = {
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
                    "value": invalid_data,
                    "headers": [],
                },
            ],
        },
    }

    schema_config = SchemaConfig(value_schema_type="JSON")

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # This should never be reached if deserializer fails
        return {"processed": True}

    # This should raise a deserialization error
    with pytest.raises(Exception) as excinfo:
        handler(kafka_event, lambda_context)

    assert "json" in str(excinfo.value).lower() or "deseriali" in str(excinfo.value).lower()


# Tests for Complex Types with Pydantic TypeAdapter


def test_kafka_consumer_with_complex_pydantic_models(kafka_event_with_json_data, lambda_context):
    """Test handling complex nested Pydantic models."""

    # Prepare a complex event with nested structure
    complex_data = {
        "name": "John Doe",
        "age": 30,
        "address": {"street": "123 Main St", "city": "Anytown", "zip": "12345"},
        "tags": ["customer", "premium"],
    }

    # Encode the complex data
    complex_encoded = base64.b64encode(json.dumps(complex_data).encode("utf-8")).decode("utf-8")

    # Create a kafka event with the complex data
    complex_event = {
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
                    "value": complex_encoded,
                    "headers": [],
                },
            ],
        },
    }

    # Define complex pydantic models
    class Address(BaseModel):
        street: str
        city: str
        zip: str

    class ComplexUser(BaseModel):
        name: str
        age: int
        address: Address
        tags: list[str]

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=ComplexUser)

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        record = next(event.records)
        result_data["value_type"] = type(record.value).__name__
        result_data["name"] = record.value.name
        result_data["age"] = record.value.age
        result_data["street"] = record.value.address.street
        result_data["city"] = record.value.address.city
        result_data["zip"] = record.value.address.zip
        result_data["tags"] = record.value.tags
        return {"processed": True}

    # Call the handler
    result = handler(complex_event, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert result_data["value_type"] == "ComplexUser"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30
    assert result_data["street"] == "123 Main St"
    assert result_data["city"] == "Anytown"
    assert result_data["zip"] == "12345"
    assert "customer" in result_data["tags"]
    assert "premium" in result_data["tags"]


def test_kafka_consumer_with_union_types(lambda_context):
    """Test handling Pydantic models with union types using TypeAdapter."""

    # Define two possible payload types
    class TextMessage(BaseModel):
        type: str = "text"
        content: str
        timestamp: int

    class ImageMessage(BaseModel):
        type: str = "image"
        url: str
        width: int
        height: int
        timestamp: int

    # Define a union type
    MessageType = TextMessage | ImageMessage

    # Create a text message event
    text_data = {"type": "text", "content": "Hello world", "timestamp": 1636718400000}

    text_encoded = base64.b64encode(json.dumps(text_data).encode("utf-8")).decode("utf-8")

    text_event = {
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
                    "value": text_encoded,
                    "headers": [],
                },
            ],
        },
    }

    # Create an image message event
    image_data = {
        "type": "image",
        "url": "https://example.com/image.jpg",
        "width": 800,
        "height": 600,
        "timestamp": 1636718500000,
    }

    image_encoded = base64.b64encode(json.dumps(image_data).encode("utf-8")).decode("utf-8")

    image_event = {
        "eventSource": "aws:kafka",
        "records": {
            "my-topic-1": [
                {
                    "topic": "my-topic-1",
                    "partition": 0,
                    "offset": 16,
                    "timestamp": 1545084650987,
                    "timestampType": "CREATE_TIME",
                    "key": None,
                    "value": image_encoded,
                    "headers": [],
                },
            ],
        },
    }

    # Create dict to capture results for text
    text_result = {}

    # Create schema config with union type
    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=MessageType)

    @kafka_consumer(schema_config=schema_config)
    def text_handler(event: ConsumerRecords, context):
        record = next(event.records)
        text_result["type"] = type(record.value).__name__
        text_result["message_type"] = record.value.type
        text_result["content"] = record.value.content
        text_result["timestamp"] = record.value.timestamp
        return {"processed": True}

    # Call the handler with text message
    text_handler(text_event, lambda_context)

    # Verify text message results
    assert text_result["type"] == "TextMessage"
    assert text_result["message_type"] == "text"
    assert text_result["content"] == "Hello world"
    assert text_result["timestamp"] == 1636718400000

    # Create dict to capture results for image
    image_result = {}

    @kafka_consumer(schema_config=schema_config)
    def image_handler(event: ConsumerRecords, context):
        record = next(event.records)
        image_result["type"] = type(record.value).__name__
        image_result["message_type"] = record.value.type
        image_result["url"] = record.value.url
        image_result["width"] = record.value.width
        image_result["height"] = record.value.height
        image_result["timestamp"] = record.value.timestamp
        return {"processed": True}

    # Call the handler with image message
    image_handler(image_event, lambda_context)

    # Verify image message results
    assert image_result["type"] == "ImageMessage"
    assert image_result["message_type"] == "image"
    assert image_result["url"] == "https://example.com/image.jpg"
    assert image_result["width"] == 800
    assert image_result["height"] == 600
    assert image_result["timestamp"] == 1636718500000


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
    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=UserSchema)

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


def test_kafka_consumer_with_key_deserialization(lambda_context, avro_schema):
    """Test deserializing both key and value with different schemas and serializers."""

    # Key schema for Avro
    key_schema = """
    {
        "type": "record",
        "name": "Key",
        "namespace": "com.example",
        "fields": [
            {"name": "id", "type": "string"}
        ]
    }
    """

    # Create Avro encoded key
    key_data = {"id": "user-123"}
    parsed_key_schema = parse_schema(key_schema)
    writer = DatumWriter(parsed_key_schema)
    bytes_writer = io.BytesIO()
    encoder = BinaryEncoder(bytes_writer)
    writer.write(key_data, encoder)
    key_encoded = base64.b64encode(bytes_writer.getvalue()).decode("utf-8")

    # Create Avro encoded value
    value_data = {"name": "John Doe", "age": 30}
    parsed_value_schema = parse_schema(avro_schema)
    writer = DatumWriter(parsed_value_schema)
    bytes_writer = io.BytesIO()
    encoder = BinaryEncoder(bytes_writer)
    writer.write(value_data, encoder)
    value_encoded = base64.b64encode(bytes_writer.getvalue()).decode("utf-8")

    # Create a kafka event with key and value
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
                    "key": key_encoded,
                    "value": value_encoded,
                    "headers": [],
                },
            ],
        },
    }

    # Define key model
    class KeyModel(BaseModel):
        id: str

    # Create dict to capture results
    key_value_result = {}

    # Create schema config with both key and value
    schema_config = SchemaConfig(
        value_schema_type="AVRO",
        value_schema=avro_schema,
        value_output_serializer=UserSchema,
        key_schema_type="AVRO",
        key_schema=key_schema,
        key_output_serializer=KeyModel,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        record = next(event.records)
        key_value_result["key_type"] = type(record.key).__name__
        key_value_result["key_id"] = record.key.id
        key_value_result["value_type"] = type(record.value).__name__
        key_value_result["value_name"] = record.value.name
        key_value_result["value_age"] = record.value.age
        return {"processed": True}

    # Call the handler
    result = handler(event, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert key_value_result["key_type"] == "KeyModel"
    assert key_value_result["key_id"] == "user-123"
    assert key_value_result["value_type"] == "UserSchema"
    assert key_value_result["value_name"] == "John Doe"
    assert key_value_result["value_age"] == 30


def test_kafka_consumer_with_different_serializers_for_key_and_value(lambda_context):
    """Test using different serializer types for key and value."""

    # Create JSON data for key and value
    key_data = {"id": "user-456"}
    value_data = {"name": "Alice Wonder", "age": 35}

    # Encode the data
    key_encoded = base64.b64encode(json.dumps(key_data).encode("utf-8")).decode("utf-8")
    value_encoded = base64.b64encode(json.dumps(value_data).encode("utf-8")).decode("utf-8")

    # Create a kafka event
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
                    "key": key_encoded,
                    "value": value_encoded,
                    "headers": [],
                },
            ],
        },
    }

    # Define models
    class KeyModel(BaseModel):
        id: str

    @dataclass
    class ValueDataClass:
        name: str
        age: int

    # Create dict to capture results
    results = {}

    # Create schema config with different serializers
    schema_config = SchemaConfig(
        value_schema_type="JSON",
        value_output_serializer=ValueDataClass,
        key_schema_type="JSON",
        key_output_serializer=KeyModel,
    )

    @kafka_consumer(schema_config=schema_config)
    def handler(event: ConsumerRecords, context):
        record = next(event.records)
        results["key_type"] = type(record.key).__name__
        results["key_id"] = record.key.id
        results["value_type"] = type(record.value).__name__
        results["value_name"] = record.value.name
        results["value_age"] = record.value.age
        return {"processed": True}

    # Call the handler
    result = handler(event, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert results["key_type"] == "KeyModel"
    assert results["key_id"] == "user-456"
    assert results["value_type"] == "ValueDataClass"
    assert results["value_name"] == "Alice Wonder"
    assert results["value_age"] == 35


def test_kafka_consumer_without_schema_config(kafka_event_with_json_data, lambda_context):
    """Test Kafka consumer when no schema config is provided."""

    # Create dict to capture results
    result_data = {}

    @kafka_consumer()
    def handler(event: ConsumerRecords, context):
        # Capture the results to verify
        record = next(event.records)
        # Should get raw base64-encoded data with no deserialization
        result_data["value_type"] = type(record.value).__name__
        return {"processed": True}

    # Call the handler
    result = handler(kafka_event_with_json_data, lambda_context)

    # Verify the results
    assert result == {"processed": True}
    assert result_data["value_type"] == "str"  # Raw base64 string


def test_kafka_consumer_with_custom_dict_class(kafka_event_with_json_data, lambda_context):
    """Test Kafka consumer with custom dict-like class with to_dict/from_dict methods."""

    # Create a custom dict-like class

    class CustomDict:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        @classmethod
        def from_dict(cls, data):
            return cls(**data)

        def to_dict(self):
            return dict(self.__dict__.items())

    # Create dict to capture results
    result_data = {}

    schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=CustomDict)

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
    assert result_data["value_type"] == "CustomDict"
    assert result_data["name"] == "John Doe"
    assert result_data["age"] == 30
