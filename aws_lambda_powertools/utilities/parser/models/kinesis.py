import json
import zlib
from typing import Dict, List, Literal, Type, Union

from pydantic import BaseModel, Field, field_validator

from aws_lambda_powertools.shared.functions import base64_decode
from aws_lambda_powertools.utilities.parser.models.cloudwatch import (
    CloudWatchLogsDecode,
)


class KinesisDataStreamRecordPayload(BaseModel):
    kinesisSchemaVersion: str = Field(
        description="The version of the Kinesis Data Streams record format.",
        examples=["1.0"],
    )
    partitionKey: str = Field(
        description="The partition key that was used to place the record in the stream.",
        examples=["user123", "device-001", "order-12345"],
    )
    sequenceNumber: str = Field(
        description="The unique sequence number for the record within the shard.",
        examples=[
            "49590338271490256608559692538361571095921575989136588898",
            "49545115243490985018280067714973144582180062593244200961",
        ],
    )
    data: Union[bytes, Type[BaseModel], BaseModel] = Field(  # base64 encoded str is parsed into bytes
        description="The data payload of the record. Base64 encoded string is automatically decoded to bytes.",
    )
    approximateArrivalTimestamp: float = Field(
        description="The approximate time that the record was inserted into the stream (Unix timestamp).",
        examples=[1428537600.0, 1609459200.5],
    )

    @field_validator("data", mode="before")
    def data_base64_decode(cls, value):
        return base64_decode(value)


class KinesisDataStreamRecord(BaseModel):
    eventSource: Literal["aws:kinesis"] = Field(
        description="The AWS service that generated the event.",
        examples=["aws:kinesis"],
    )
    eventVersion: str = Field(description="The version of the event schema.", examples=["1.0"])
    eventID: str = Field(
        description="A unique identifier for the event.",
        examples=["shardId-000000000006:49590338271490256608559692538361571095921575989136588898"],
    )
    eventName: Literal["aws:kinesis:record"] = Field(
        description="The name of the event type.",
        examples=["aws:kinesis:record"],
    )
    invokeIdentityArn: str = Field(
        description="The ARN of the IAM role used to invoke the Lambda function.",
        examples=["arn:aws:iam::123456789012:role/lambda-kinesis-role"],
    )
    awsRegion: str = Field(
        description="The AWS region where the Kinesis stream is located.",
        examples=["us-east-1", "us-west-2", "eu-west-1"],
    )
    eventSourceARN: str = Field(
        description="The ARN of the Kinesis stream that generated the event.",
        examples=["arn:aws:kinesis:us-east-1:123456789012:stream/my-stream"],
    )
    kinesis: KinesisDataStreamRecordPayload = Field(description="The Kinesis-specific data for the record.")

    def decompress_zlib_record_data_as_json(self) -> Dict:
        """Decompress Kinesis Record bytes data zlib compressed to JSON"""
        if not isinstance(self.kinesis.data, bytes):
            raise ValueError("We can only decompress bytes data, not custom models.")

        return json.loads(zlib.decompress(self.kinesis.data, zlib.MAX_WBITS | 32))


class KinesisDataStreamModel(BaseModel):
    Records: List[KinesisDataStreamRecord] = Field(
        description="A list of Kinesis Data Stream records that triggered the Lambda function.",
        examples=[[]],
    )


def extract_cloudwatch_logs_from_event(event: KinesisDataStreamModel) -> List[CloudWatchLogsDecode]:
    return [CloudWatchLogsDecode(**record.decompress_zlib_record_data_as_json()) for record in event.Records]


def extract_cloudwatch_logs_from_record(record: KinesisDataStreamRecord) -> CloudWatchLogsDecode:
    return CloudWatchLogsDecode(**record.decompress_zlib_record_data_as_json())
