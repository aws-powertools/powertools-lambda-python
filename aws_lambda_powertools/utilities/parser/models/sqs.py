from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser.types import Literal, Model


class SqsAttributesModel(BaseModel):
    ApproximateReceiveCount: str
    ApproximateFirstReceiveTimestamp: datetime
    MessageDeduplicationId: Optional[str]
    MessageGroupId: Optional[str]
    SenderId: str
    SentTimestamp: datetime
    SequenceNumber: Optional[str]
    AWSTraceHeader: Optional[str]


class SqsMsgAttributeModel(BaseModel):
    stringValue: Optional[str]
    binaryValue: Optional[str]
    stringListValues: List[str] = []
    binaryListValues: List[str] = []
    dataType: str

    # context on why it's commented: https://github.com/awslabs/aws-lambda-powertools-python/pull/118
    # Amazon SQS supports the logical data types String, Number, and Binary with optional custom data type
    # labels with the format .custom-data-type.
    # https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-message-metadata.html#sqs-message-attributes
    # @validator("dataType")
    # def valid_type(cls, v):  # noqa: VNE001,E800 # noqa: E800
    #     pattern = re.compile("Number.*|String.*|Binary.*") # noqa: E800
    #     if not pattern.match(v): # noqa: E800
    #         raise TypeError("data type is invalid") # noqa: E800
    #     return v # noqa: E800
    #
    # # validate that dataType and value are not None and match
    # @root_validator
    # def check_str_and_binary_values(cls, values): # noqa: E800
    #     binary_val, str_val = values.get("binaryValue", ""), values.get("stringValue", "") # noqa: E800
    #     data_type = values.get("dataType") # noqa: E800
    #     if not str_val and not binary_val: # noqa: E800
    #         raise TypeError("both binaryValue and stringValue are missing") # noqa: E800
    #     if data_type.startswith("Binary") and not binary_val: # noqa: E800
    #         raise TypeError("binaryValue is missing") # noqa: E800
    #     if (data_type.startswith("String") or data_type.startswith("Number")) and not str_val: # noqa: E800
    #         raise TypeError("stringValue is missing") # noqa: E800
    #     return values # noqa: E800


class SqsRecordModel(BaseModel):
    messageId: str
    receiptHandle: str
    body: Union[str, Model]
    attributes: SqsAttributesModel
    messageAttributes: Dict[str, SqsMsgAttributeModel]
    md5OfBody: str
    md5OfMessageAttributes: Optional[str]
    eventSource: Literal["aws:sqs"]
    eventSourceARN: str
    awsRegion: str


class SqsModel(BaseModel):
    Records: List[SqsRecordModel]
