import json
from typing import List, Optional

from pydantic import BaseModel, Field, PositiveInt, field_validator

from aws_lambda_powertools.shared.functions import base64_decode
from aws_lambda_powertools.utilities.parser.models import KinesisFirehoseRecordMetadata

from .sqs import SqsRecordModel


class KinesisFirehoseSqsRecord(BaseModel):
    data: SqsRecordModel = Field(description="The SQS record data that was delivered through Kinesis Data Firehose.")
    recordId: str = Field(
        description="A unique identifier for the record within the batch.",
        examples=["49546986683135544286507457936321625675700192471156785154"],
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
        # Firehose payload is encoded
        return json.loads(base64_decode(value))


class KinesisFirehoseSqsModel(BaseModel):
    invocationId: str = Field(
        description="A unique identifier for the Lambda invocation.",
        examples=["invocationIdExample", "12345678-1234-1234-1234-123456789012"],
    )
    deliveryStreamArn: str = Field(
        description="The ARN of the Kinesis Data Firehose delivery stream.",
        examples=["arn:aws:firehose:us-east-1:123456789012:deliverystream/my-sqs-delivery-stream"],
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
    records: List[KinesisFirehoseSqsRecord] = Field(
        description="A list of SQS records delivered through Kinesis Data Firehose \
        to be processed by the Lambda function.",
        examples=[[]],
    )
