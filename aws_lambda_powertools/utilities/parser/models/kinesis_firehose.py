from typing import List, Optional, Type, Union

from pydantic import BaseModel, Field, PositiveInt, field_validator

from aws_lambda_powertools.shared.functions import base64_decode


class KinesisFirehoseRecordMetadata(BaseModel):
    shardId: str = Field(
        description="The shard ID of the Kinesis stream record.",
        examples=["shardId-000000000000", "shardId-000000000001"],
    )
    partitionKey: str = Field(
        description="The partition key of the Kinesis stream record.",
        examples=["user123", "device-001", "transaction-456"],
    )
    approximateArrivalTimestamp: PositiveInt = Field(
        description="The approximate time when the record arrived in the Kinesis stream \
        (Unix timestamp in milliseconds).",
        examples=[1428537600000, 1609459200500],
    )
    sequenceNumber: str = Field(
        description="The sequence number of the Kinesis stream record.",
        examples=["49590338271490256608559692538361571095921575989136588898"],
    )
    subsequenceNumber: int = Field(
        description="The subsequence number for records that share the same sequence number.",
        examples=[0, 1, 2],
    )


class KinesisFirehoseRecord(BaseModel):
    data: Union[bytes, Type[BaseModel]] = Field(  # base64 encoded str is parsed into bytes
        description="The data payload of the record. Base64 encoded string is automatically decoded to bytes.",
    )
    recordId: str = Field(
        description="A unique identifier for the record within the batch.",
        examples=[
            "49546986683135544286507457936321625675700192471156785154",
            "49546986683135544286507457936321625675700192471156785155",
        ],
    )
    approximateArrivalTimestamp: PositiveInt = Field(
        description="The approximate time when the record arrived in Kinesis Data Firehose \
        (Unix timestamp in milliseconds).",
        examples=[1428537600000, 1609459200500],
    )
    kinesisRecordMetadata: Optional[KinesisFirehoseRecordMetadata] = Field(
        None,
        description="Metadata about the original Kinesis stream record \
        (only present when the delivery stream source is a Kinesis stream).",
    )

    @field_validator("data", mode="before")
    def data_base64_decode(cls, value):
        return base64_decode(value)


class KinesisFirehoseModel(BaseModel):
    invocationId: str = Field(
        description="A unique identifier for the Lambda invocation.",
        examples=["invocationIdExample", "12345678-1234-1234-1234-123456789012"],
    )
    deliveryStreamArn: str = Field(
        description="The ARN of the Kinesis Data Firehose delivery stream.",
        examples=["arn:aws:firehose:us-east-1:123456789012:deliverystream/my-delivery-stream"],
    )
    region: str = Field(
        description="The AWS region where the delivery stream is located.",
        examples=["us-east-1", "us-west-2", "eu-west-1"],
    )
    sourceKinesisStreamArn: Optional[str] = Field(
        None,
        description="The ARN of the source Kinesis stream \
        (only present when the delivery stream source is a Kinesis stream).",
        examples=["arn:aws:kinesis:us-east-1:123456789012:stream/my-source-stream"],
    )
    records: List[KinesisFirehoseRecord] = Field(
        description="A list of records to be processed by the Lambda function.",
        examples=[[]],
    )
