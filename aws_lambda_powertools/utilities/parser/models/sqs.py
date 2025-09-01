from datetime import datetime
from typing import Dict, List, Literal, Optional, Sequence, Type, Union

from pydantic import BaseModel, Field


class SqsAttributesModel(BaseModel):
    ApproximateReceiveCount: str = Field(
        description="The number of times a message has been received across all queues but not deleted.",
        examples=["1", "2"],
    )
    ApproximateFirstReceiveTimestamp: datetime = Field(
        description="The time the message was first received from the queue (epoch time in milliseconds).",
        examples=["1545082649185", "1545082650649", "1713185156612"],
    )
    MessageDeduplicationId: Optional[str] = Field(
        default=None,
        description="Returns the value provided by the producer that calls the SendMessage action.",
        examples=["msg-dedup-12345", "unique-msg-abc123", None],
    )
    MessageGroupId: Optional[str] = Field(
        default=None,
        description="Returns the value provided by the producer that calls the SendMessage action.",
        examples=["order-processing", "user-123-updates", None],
    )
    SenderId: str = Field(
        description="The user ID for IAM users or the role ID for IAM roles that sent the message.",
        examples=["AIDAIENQZJOLO23YVJ4VO", "AMCXIENQZJOLO23YVJ4VO"],
    )
    SentTimestamp: datetime = Field(
        description="The time the message was sent to the queue (epoch time in milliseconds).",
        examples=["1545082649183", "1545082650636", "1713185156609"],
    )
    SequenceNumber: Optional[str] = Field(
        default=None,
        description="Returns the value provided by Amazon SQS.",
        examples=["18849496460467696128", "18849496460467696129", None],
    )
    AWSTraceHeader: Optional[str] = Field(
        default=None,
        description="The AWS X-Ray trace header for request tracing.",
        examples=["Root=1-5e1b4151-5ac6c58239c1e5b4", None],
    )
    DeadLetterQueueSourceArn: Optional[str] = Field(
        default=None,
        description="The ARN of the dead-letter queue from which the message was moved.",
        examples=["arn:aws:sqs:eu-central-1:123456789012:sqs-redrive-SampleQueue-RNvLCpwGmLi7", None],
    )


class SqsMsgAttributeModel(BaseModel):
    stringValue: Optional[str] = Field(
        default=None,
        description="The string value of the message attribute.",
        examples=["100", "active", "user-12345", None],
    )
    binaryValue: Optional[str] = Field(
        default=None,
        description="The binary value of the message attribute, base64-encoded.",
        examples=["base64Str", "SGVsbG8gV29ybGQ=", None],
    )
    stringListValues: List[str] = Field(
        default=[],
        description="A list of string values for the message attribute.",
        examples=[["item1", "item2"], ["tag1", "tag2", "tag3"], []],
    )
    binaryListValues: List[str] = Field(
        default=[],
        description="A list of binary values for the message attribute, each base64-encoded.",
        examples=[["dmFsdWUx", "dmFsdWUy"], ["aGVsbG8="], []],
    )
    dataType: str = Field(
        description="The data type of the message attribute (String, Number, Binary, or custom data type).",
        examples=["String", "Number", "Binary", "String.custom", "Number.float"],
    )

    # context on why it's commented: https://github.com/aws-powertools/powertools-lambda-python/pull/118
    # Amazon SQS supports the logical data types String, Number, and Binary with optional custom data type
    # labels with the format .custom-data-type.
    # https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-message-metadata.html#sqs-message-attributes
    # @validator("dataType")
    # def valid_type(cls, v):  # noqa: VNE001,ERA001 # noqa: ERA001
    #     pattern = re.compile("Number.*|String.*|Binary.*") # noqa: ERA001
    #     if not pattern.match(v): # noqa: ERA001
    #         raise TypeError("data type is invalid") # noqa: ERA001
    #     return v # noqa: ERA001
    #
    # # validate that dataType and value are not None and match
    # @root_validator
    # def check_str_and_binary_values(cls, values): # noqa: ERA001
    #     binary_val, str_val = values.get("binaryValue", ""), values.get("stringValue", "") # noqa: ERA001
    #     data_type = values.get("dataType") # noqa: ERA001
    #     if not str_val and not binary_val: # noqa: ERA001
    #         raise TypeError("both binaryValue and stringValue are missing") # noqa: ERA001
    #     if data_type.startswith("Binary") and not binary_val: # noqa: ERA001
    #         raise TypeError("binaryValue is missing") # noqa: ERA001
    #     if (data_type.startswith("String") or data_type.startswith("Number")) and not str_val: # noqa: ERA001
    #         raise TypeError("stringValue is missing") # noqa: ERA001
    #     return values # noqa: ERA001


class SqsRecordModel(BaseModel):
    messageId: str = Field(
        description="A unique identifier for the message. A MessageId is considered unique across all AWS accounts.",
        examples=[
            "059f36b4-87a3-44ab-83d2-661975830a7d",
            "2e1424d4-f796-459a-8184-9c92662be6da",
            "db37cc61-1bb0-4e77-b6f3-7cf87f44a72a",
        ],
    )
    receiptHandle: str = Field(
        description="An identifier associated with the act of receiving the message, used for message deletion.",
        examples=[
            "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a...",
            "AQEBzWwaftRI0KuVm4tP+/7q1rGgNqicHq...",
        ],
    )
    body: Union[str, Type[BaseModel], BaseModel] = Field(
        description="The message's contents (not URL-encoded). Can be plain text or JSON.",
        examples=[
            "Test message.",
            '{"message": "foo1"}',
            "hello world",
        ],
    )
    attributes: SqsAttributesModel = Field(
        description="A map of the attributes requested in ReceiveMessage to their respective values.",
    )
    messageAttributes: Dict[str, SqsMsgAttributeModel] = Field(
        description="User-defined message attributes as key-value pairs.",
        examples=[
            {"testAttr": {"stringValue": "100", "binaryValue": "base64Str", "dataType": "Number"}},
            {},
        ],
    )
    md5OfBody: str = Field(
        description="An MD5 digest of the non-URL-encoded message body string.",
        examples=[
            "e4e68fb7bd0e697a0ae8f1bb342846b3",
            "6a204bd89f3c8348afd5c77c717a097a",
        ],
    )
    md5OfMessageAttributes: Optional[str] = Field(
        default=None,
        description="An MD5 digest of the non-URL-encoded message attribute string.",
        examples=[
            "00484c68...59e48fb7",
            "b25f48e8...f4e4f0bb",
            None,
        ],
    )
    eventSource: Literal["aws:sqs"] = Field(
        description="The AWS service that invoked the function.",
        examples=["aws:sqs"],
    )
    eventSourceARN: str = Field(
        description="The Amazon Resource Name (ARN) of the SQS queue.",
        examples=[
            "arn:aws:sqs:us-east-2:123456789012:my-queue",
            "arn:aws:sqs:eu-central-1:123456789012:sqs-redrive-SampleDLQ-Emgp9MFSLBZm",
        ],
    )
    awsRegion: str = Field(
        description="The AWS region where the SQS queue is located.",
        examples=["us-east-1", "us-east-2", "eu-central-1"],
    )


class SqsModel(BaseModel):
    Records: Sequence[SqsRecordModel] = Field(
        description="A list of SQS message records included in the event.",
        examples=[[{"messageId": "059f36b4-87a3-44ab-83d2-661975830a7d", "body": "Test message."}]],
    )
