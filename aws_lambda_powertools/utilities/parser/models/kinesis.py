from typing import List, Type, Union

from pydantic import BaseModel, validator

from aws_lambda_powertools.shared.functions import base64_decode
from aws_lambda_powertools.utilities.parser.types import Literal


class KinesisDataStreamRecordPayload(BaseModel):
    kinesisSchemaVersion: str
    partitionKey: str
    sequenceNumber: str
    data: Union[bytes, Type[BaseModel]]  # base64 encoded str is parsed into bytes
    approximateArrivalTimestamp: float

    @validator("data", pre=True, allow_reuse=True)
    def data_base64_decode(cls, value):
        return base64_decode(value)


class KinesisDataStreamRecord(BaseModel):
    eventSource: Literal["aws:kinesis"]
    eventVersion: str
    eventID: str
    eventName: Literal["aws:kinesis:record"]
    invokeIdentityArn: str
    awsRegion: str
    eventSourceARN: str
    kinesis: KinesisDataStreamRecordPayload


class KinesisDataStreamModel(BaseModel):
    Records: List[KinesisDataStreamRecord]
