import base64
import json
import zlib
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, validator


class CloudWatchLogsLogEvent(BaseModel):
    id: str  # noqa AA03 VNE003
    timestamp: datetime
    message: str


class CloudWatchLogsDecode(BaseModel):
    messageType: str
    owner: str
    logGroup: str
    logStream: str
    subscriptionFilters: List[str]
    logEvents: List[CloudWatchLogsLogEvent]


class CloudWatchLogsData(BaseModel):
    decoded_data: CloudWatchLogsDecode = Field(None, alias="data")

    @validator("decoded_data", pre=True)
    def prepare_data(cls, value):
        try:
            payload = base64.b64decode(value)
            uncompressed = zlib.decompress(payload, zlib.MAX_WBITS | 32)
            return json.loads(uncompressed.decode("UTF-8"))
        except Exception:
            raise ValueError("unable to decompress data")


class CloudWatchLogsModel(BaseModel):
    awslogs: CloudWatchLogsData
