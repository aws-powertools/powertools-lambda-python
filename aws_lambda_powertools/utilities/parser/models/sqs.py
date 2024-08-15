from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import Literal, Sequence

from pydantic import BaseModel


class SqsAttributesModel(BaseModel):
    ApproximateReceiveCount: str
    ApproximateFirstReceiveTimestamp: datetime
    MessageDeduplicationId: str | None = None
    MessageGroupId: str | None = None
    SenderId: str
    SentTimestamp: datetime
    SequenceNumber: str | None = None
    AWSTraceHeader: str | None = None
    DeadLetterQueueSourceArn: str | None = None


class SqsMsgAttributeModel(BaseModel):
    stringValue: str | None = None
    binaryValue: str | None = None
    stringListValues: list[str] = []
    binaryListValues: list[str] = []
    dataType: str

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
    messageId: str
    receiptHandle: str
    body: str | type[BaseModel] | BaseModel
    attributes: SqsAttributesModel
    messageAttributes: dict[str, SqsMsgAttributeModel]
    md5OfBody: str
    md5OfMessageAttributes: str | None = None
    eventSource: Literal["aws:sqs"]
    eventSourceARN: str
    awsRegion: str


class SqsModel(BaseModel):
    Records: Sequence[SqsRecordModel]
