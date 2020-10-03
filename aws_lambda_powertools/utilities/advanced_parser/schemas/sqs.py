import re
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, root_validator, validator
from typing_extensions import Literal


class SqsAttributesSchema(BaseModel):
    ApproximateReceiveCount: str
    ApproximateFirstReceiveTimestamp: datetime
    MessageDeduplicationId: Optional[str]
    MessageGroupId: Optional[str]
    SenderId: str
    SentTimestamp: datetime
    SequenceNumber: Optional[str]
    AWSTraceHeader: Optional[str]


class SqsMsgAttributeSchema(BaseModel):
    stringValue: Optional[str]
    binaryValue: Optional[str]
    stringListValues: List[str] = []
    binaryListValues: List[str] = []
    dataType: str

    # Amazon SQS supports the logical data types String, Number, and Binary with optional custom data type
    # labels with the format .custom-data-type.
    # https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-message-metadata.html#sqs-message-attributes
    @validator("dataType")
    def valid_type(cls, v):  # noqa: VNE001
        pattern = re.compile("Number.*|String.*|Binary.*")
        if not pattern.match(v):
            raise TypeError("data type is invalid")
        return v

    # validate that dataType and value are not None and match 
    @root_validator
    def check_str_and_binary_values(cls, values):
        binary_val, str_val = values.get("binaryValue", ""), values.get("stringValue", "")
        dataType = values.get("dataType")
        if not str_val and not binary_val:
            raise TypeError("both binaryValue and stringValue are missing")
        if dataType.startswith("Binary") and not binary_val:
            raise TypeError("binaryValue is missing")
        if (dataType.startswith("String") or dataType.startswith("Number")) and not str_val:
            raise TypeError("stringValue is missing")
        return values


class SqsRecordSchema(BaseModel):
    messageId: str
    receiptHandle: str
    body: str
    attributes: SqsAttributesSchema
    messageAttributes: Dict[str, SqsMsgAttributeSchema]
    md5OfBody: str
    md5OfMessageAttributes: Optional[str]
    eventSource: Literal["aws:sqs"]
    eventSourceARN: str
    awsRegion: str


class SqsSchema(BaseModel):
    Records: List[SqsRecordSchema]
