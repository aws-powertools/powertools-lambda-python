import base64
import json
import logging
import zlib
from datetime import datetime
from typing import List, Optional, Type, Union

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class CloudWatchLogsLogEvent(BaseModel):
    id: str = Field(
        description="Unique identifier for the log event within the batch.",
        examples=["eventId1", "abc123def456"],
    )
    timestamp: datetime = Field(
        description="The time when the event occurred in milliseconds since Jan 1, 1970 00:00:00 UTC.",
        examples=[1673779200000],
    )
    message: Union[str, Type[BaseModel]] = Field(
        description="The actual log message string or structured JSON payload emitted by the service or application.",
        examples=["This is a sample log message", '{"statusCode":200,"path":"/hello"}'],
    )


class CloudWatchLogsDecode(BaseModel):
    messageType: str = Field(
        description="The type of CloudWatch Logs message.",
        examples=["DATA_MESSAGE", "CONTROL_MESSAGE"],
    )
    owner: str = Field(description="The AWS account ID of the originating log data.", examples=["123456789012"])
    logGroup: str = Field(
        description="The name of the log group that contains the log stream.",
        examples=["/aws/lambda/my-function", "/aws/apigateway/my-api"],
    )
    logStream: str = Field(
        description="The name of the log stream that stores the log events.",
        examples=["2023/01/15/[$LATEST]abcdef1234567890", "i-1234567890abcdef0"],
    )
    subscriptionFilters: List[str] = Field(
        description="List of subscription filter names associated with the log group.",
        examples=[["LambdaStream_cloudwatch", "AlertFilter"]],
    )
    logEvents: List[CloudWatchLogsLogEvent] = Field(
        description="Array of log events included in the message.",
        examples=[[{"id": "eventId1", "timestamp": 1673779200000, "message": "Sample log line"}]],
    )
    policyLevel: Optional[str] = Field(
        default=None,
        description="Optional field specifying the policy level applied to the subscription filter, if present.",
        examples=["ACCOUNT", "LOG_GROUP"],
    )


class CloudWatchLogsData(BaseModel):
    decoded_data: CloudWatchLogsDecode = Field(
        ...,
        alias="data",
        description="Decoded CloudWatch log data payload after base64 decoding and decompression.",
    )

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
    awslogs: CloudWatchLogsData = Field(
        description="Top-level CloudWatch Logs model containing the AWS logs data section.",
    )
