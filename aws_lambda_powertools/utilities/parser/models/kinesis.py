import base64
import logging
from binascii import Error as BinAsciiError
from typing import List

from pydantic import BaseModel, validator
from pydantic.types import PositiveInt

from ..types import Literal

logger = logging.getLogger(__name__)


class KinesisDataStreamRecordPayload(BaseModel):
    kinesisSchemaVersion: str
    partitionKey: str
    sequenceNumber: PositiveInt
    data: bytes  # base64 encoded str is parsed into bytes
    approximateArrivalTimestamp: float

    @validator("data", pre=True, allow_reuse=True)
    def data_base64_decode(cls, value):
        try:
            logger.debug("Decoding base64 Kinesis data record before parsing")
            return base64.b64decode(value)
        except (BinAsciiError, TypeError):
            raise ValueError("base64 decode failed")


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
