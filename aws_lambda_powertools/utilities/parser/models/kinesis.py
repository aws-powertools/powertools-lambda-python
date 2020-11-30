import base64
from binascii import Error as BinAsciiError
from typing import List

from pydantic import BaseModel, validator
from pydantic.types import PositiveInt
from typing_extensions import Literal


class KinesisStreamRecordPayload(BaseModel):
    kinesisSchemaVersion: str
    partitionKey: str
    sequenceNumber: PositiveInt
    data: bytes  # base64 encoded str is parsed into bytes
    approximateArrivalTimestamp: float

    @validator("data", pre=True)
    def data_base64_decode(cls, value):
        try:
            return base64.b64decode(value)
        except (BinAsciiError, TypeError):
            raise ValueError("base64 decode failed")


class KinesisStreamRecord(BaseModel):
    eventSource: Literal["aws:kinesis"]
    eventVersion: str
    eventID: str
    eventName: Literal["aws:kinesis:record"]
    invokeIdentityArn: str
    awsRegion: str
    eventSourceARN: str
    kinesis: KinesisStreamRecordPayload


class KinesisStreamModel(BaseModel):
    Records: List[KinesisStreamRecord]
