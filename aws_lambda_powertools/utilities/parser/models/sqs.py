from datetime import datetime
from typing import Dict, List, Optional, Sequence, Type, Union

from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser.types import Literal


class SqsAttributesModel(BaseModel):
    ApproximateReceiveCount: str
    ApproximateFirstReceiveTimestamp: datetime
    MessageDeduplicationId: Optional[str] = None
    MessageGroupId: Optional[str] = None
    SenderId: str
    SentTimestamp: datetime
    SequenceNumber: Optional[str] = None
    AWSTraceHeader: Optional[str] = None
    DeadLetterQueueSourceArn: Optional[str] = None


class SqsMsgAttributeModel(BaseModel):
    stringValue: Optional[str] = None
    binaryValue: Optional[str] = None
    stringListValues: List[str] = []
    binaryListValues: List[str] = []
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
    body: Union[str, Type[BaseModel], BaseModel]
    attributes: SqsAttributesModel
    messageAttributes: Dict[str, SqsMsgAttributeModel]
    md5OfBody: str
    md5OfMessageAttributes: Optional[str] = None
    eventSource: Literal["aws:sqs"]
    eventSourceARN: str
    awsRegion: str


class SqsModel(BaseModel):
    Records: Sequence[SqsRecordModel]
