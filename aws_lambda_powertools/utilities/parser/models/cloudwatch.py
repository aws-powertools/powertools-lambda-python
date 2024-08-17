import base64
import json
import logging
import zlib
from datetime import datetime
from typing import List, Optional, Type, Union

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class CloudWatchLogsLogEvent(BaseModel):
    id: str  # noqa AA03 VNE003
    timestamp: datetime
    message: Union[str, Type[BaseModel]]


class CloudWatchLogsDecode(BaseModel):
    messageType: str
    owner: str
    logGroup: str
    logStream: str
    subscriptionFilters: List[str]
    logEvents: List[CloudWatchLogsLogEvent]
    policyLevel: Optional[str] = None


class CloudWatchLogsData(BaseModel):
    decoded_data: CloudWatchLogsDecode = Field(None, alias="data")

    @field_validator("decoded_data", mode="before")
    def prepare_data(cls, value):
        try:
            logger.debug("Decoding base64 cloudwatch log data before parsing")
            payload = base64.b64decode(value)
            logger.debug("Decompressing cloudwatch log data before parsing")
            uncompressed = zlib.decompress(payload, zlib.MAX_WBITS | 32)
            return json.loads(uncompressed.decode("utf-8"))
        except Exception:
            raise ValueError("unable to decompress data")


class CloudWatchLogsModel(BaseModel):
    awslogs: CloudWatchLogsData
