from datetime import datetime
from typing import Dict, List, Literal, Optional, Type, Union

from pydantic import BaseModel, Field, field_validator

from aws_lambda_powertools.shared.functions import base64_decode, bytes_to_string, decode_header_bytes

SERVERS_DELIMITER = ","


class KafkaRecordSchemaMetadata(BaseModel):
    dataFormat: str = Field(
        description="The data format of the schema (e.g., AVRO, JSON).",
        examples=["AVRO", "JSON", "PROTOBUF"],
    )
    schemaId: str = Field(
        description="The unique identifier of the schema.",
        examples=["1234", "5678", "schema-abc-123"],
    )


class KafkaRecordModel(BaseModel):
    topic: str = Field(
        description="The Kafka topic name from which the record originated.",
        examples=["mytopic", "user-events", "order-processing", "mymessage-with-unsigned"],
    )
    partition: int = Field(
        description="The partition number within the topic from which the record was consumed.",
        examples=[0, 1, 5, 10],
    )
    offset: int = Field(
        description="The offset of the record within the partition.",
        examples=[15, 123, 456789, 1000000],
    )
    timestamp: datetime = Field(
        description="The timestamp of the record.",
        examples=[1545084650987, 1640995200000, 1672531200000],
    )
    timestampType: str = Field(
        description="The type of timestamp (CREATE_TIME or LOG_APPEND_TIME).",
        examples=["CREATE_TIME", "LOG_APPEND_TIME"],
    )
    key: Optional[bytes] = Field(
        default=None,
        description="The message key, base64-encoded. Can be null for messages without keys.",
        examples=["cmVjb3JkS2V5", "dXNlci0xMjM=", "b3JkZXItNDU2", None],
    )
    value: Union[str, Type[BaseModel]] = Field(
        description="The message value, base64-encoded.",
        examples=[
            "eyJrZXkiOiJ2YWx1ZSJ9",
            "eyJtZXNzYWdlIjogIkhlbGxvIEthZmthIn0=",
            "eyJ1c2VyX2lkIjogMTIzLCAiYWN0aW9uIjogImxvZ2luIn0=",
        ],
    )
    headers: List[Dict[str, bytes]] = Field(
        description="A list of message headers as key-value pairs with byte array values.",
        examples=[
            [{"headerKey": [104, 101, 97, 100, 101, 114, 86, 97, 108, 117, 101]}],
            [{"contentType": [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115, 111, 110]}],
            [],
        ],
    )
    keySchemaMetadata: Optional[KafkaRecordSchemaMetadata] = Field(
        default=None,
        description="Schema metadata for the message key when using schema registry.",
        examples=[{"dataFormat": "AVRO", "schemaId": "1234"}, None],
    )
    valueSchemaMetadata: Optional[KafkaRecordSchemaMetadata] = Field(
        default=None,
        description="Schema metadata for the message value when using schema registry.",
        examples=[{"dataFormat": "AVRO", "schemaId": "1234"}, None],
    )

    # key is optional; only decode if not None
    @field_validator("key", mode="before")
    def decode_key(cls, value):
        return base64_decode(value) if value is not None else value

    @field_validator("value", mode="before")
    def data_base64_decode(cls, value):
        as_bytes = base64_decode(value)
        return bytes_to_string(as_bytes)

    @field_validator("headers", mode="before")
    def decode_headers_list(cls, value):
        for header in value:
            for key, values in header.items():
                header[key] = decode_header_bytes(values)
        return value


class KafkaBaseEventModel(BaseModel):
    bootstrapServers: List[str] = Field(
        description="A list of Kafka bootstrap servers (broker endpoints).",
        examples=[
            ["b-2.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092"],
            [
                "b-1.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092",
                "b-2.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092",
            ],
        ],
    )
    records: Dict[str, List[KafkaRecordModel]] = Field(
        description="A dictionary mapping topic-partition combinations to lists of Kafka records.",
        examples=[
            {"mytopic-0": [{"topic": "mytopic", "partition": 0, "offset": 15}]},
            {"user-events-1": [{"topic": "user-events", "partition": 1, "offset": 123}]},
        ],
    )

    @field_validator("bootstrapServers", mode="before")
    def split_servers(cls, value):
        return value.split(SERVERS_DELIMITER) if value else None


class KafkaSelfManagedEventModel(KafkaBaseEventModel):
    """Self-managed Apache Kafka event trigger
    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-kafka.html
    """

    eventSource: Literal["SelfManagedKafka"] = Field(
        description="The event source identifier for self-managed Kafka.",
        examples=["SelfManagedKafka"],
    )


class KafkaMskEventModel(KafkaBaseEventModel):
    """Fully-managed AWS Apache Kafka event trigger
    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-msk.html
    """

    eventSource: Literal["aws:kafka"] = Field(
        description="The AWS service that invoked the function.",
        examples=["aws:kafka"],
    )
    eventSourceArn: str = Field(
        description="The Amazon Resource Name (ARN) of the MSK cluster.",
        examples=[
            "arn:aws:kafka:us-east-1:0123456789019:cluster/SalesCluster/abcd1234-abcd-cafe-abab-9876543210ab-4",
            "arn:aws:kafka:eu-central-1:123456789012:cluster/MyCluster/xyz789-1234-5678-90ab-cdef12345678-2",
        ],
    )
