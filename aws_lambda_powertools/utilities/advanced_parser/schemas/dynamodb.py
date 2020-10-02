from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, root_validator
from typing_extensions import Literal


class DynamoScheme(BaseModel):
    ApproximateCreationDateTime: Optional[date]
    Keys: Dict[str, Dict[str, Any]]
    NewImage: Optional[Dict[str, Any]]
    OldImage: Optional[Dict[str, Any]]
    SequenceNumber: str
    SizeBytes: int
    StreamViewType: Literal["NEW_AND_OLD_IMAGES", "KEYS_ONLY", "NEW_IMAGE", "OLD_IMAGE"]

    # since both images are optional, they can both be None. However, at least one must
    # exist in a legal schema of NEW_AND_OLD_IMAGES type
    @root_validator
    def check_one_image_exists(cls, values):
        newimg, oldimg = values.get("NewImage"), values.get("OldImage")
        stream_type = values.get("StreamViewType")
        if stream_type == "NEW_AND_OLD_IMAGES" and not newimg and not oldimg:
            raise TypeError("DynamoDB streams schema failed validation, missing both new & old stream images")
        return values


class UserIdentity(BaseModel):
    type: Literal["Service"]  # noqa: VNE003, A003
    principalId: Literal["dynamodb.amazonaws.com"]


class DynamoRecordSchema(BaseModel):
    eventID: str
    eventName: Literal["INSERT", "MODIFY", "REMOVE"]
    eventVersion: float
    eventSource: Literal["aws:dynamodb"]
    awsRegion: str
    eventSourceARN: str
    dynamodb: DynamoScheme
    userIdentity: Optional[UserIdentity]


class DynamoDBSchema(BaseModel):
    Records: List[DynamoRecordSchema]
