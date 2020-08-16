from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, root_validator
from typing_extensions import Literal


class DynamoScheme(BaseModel):
    ApproximateCreationDateTime: date
    Keys: Dict[Literal["id"], Dict[Literal["S"], str]]
    NewImage: Optional[Dict[str, Any]] = {}
    OldImage: Optional[Dict[str, Any]] = {}
    SequenceNumber: str
    SizeBytes: int
    StreamViewType: Literal["NEW_AND_OLD_IMAGES", "KEYS_ONLY", "NEW_IMAGE", "OLD_IMAGE"]

    @root_validator
    def check_one_image_exists(cls, values):
        newimg, oldimg = values.get("NewImage"), values.get("OldImage")
        stream_type = values.get("StreamViewType")
        if stream_type == "NEW_AND_OLD_IMAGES" and not newimg and not oldimg:
            raise TypeError("DynamoDB streams schema failed validation, missing both new & old stream images")
        return values


class DynamoRecordSchema(BaseModel):
    eventID: str
    eventName: Literal["INSERT", "MODIFY", "REMOVE"]
    eventVersion: float
    eventSource: Literal["aws:dynamodb"]
    awsRegion: str
    eventSourceARN: str
    dynamodb: DynamoScheme


class DynamoDBSchema(BaseModel):
    Records: List[DynamoRecordSchema]


class EventBridgeSchema(BaseModel):
    version: str
    id: str  # noqa: A003,VNE003
    source: str
    account: int
    time: datetime
    region: str
    resources: List[str]
    detail: Dict[str, Any]


class SqsSchema(BaseModel):
    todo: str


class SnsSchema(BaseModel):
    todo: str
