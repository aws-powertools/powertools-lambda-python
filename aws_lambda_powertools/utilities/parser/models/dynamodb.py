from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import Any, Literal

from pydantic import BaseModel, field_validator

from aws_lambda_powertools.shared.dynamodb_deserializer import TypeDeserializer

_DESERIALIZER = TypeDeserializer()


class DynamoDBStreamChangedRecordModel(BaseModel):
    ApproximateCreationDateTime: datetime | None = None
    Keys: dict[str, Any]
    NewImage: dict[str, Any] | type[BaseModel] | BaseModel | None = None
    OldImage: dict[str, Any] | type[BaseModel] | BaseModel | None = None
    SequenceNumber: str
    SizeBytes: int
    StreamViewType: Literal["NEW_AND_OLD_IMAGES", "KEYS_ONLY", "NEW_IMAGE", "OLD_IMAGE"]

    # context on why it's commented: https://github.com/aws-powertools/powertools-lambda-python/pull/118
    # since both images are optional, they can both be None. However, at least one must
    # exist in a legal model of NEW_AND_OLD_IMAGES type
    # @root_validator
    # def check_one_image_exists(cls, values): # noqa: ERA001
    #     new_img, old_img = values.get("NewImage"), values.get("OldImage") # noqa: ERA001
    #     stream_type = values.get("StreamViewType") # noqa: ERA001
    #     if stream_type == "NEW_AND_OLD_IMAGES" and not new_img and not old_img: # noqa: ERA001
    #         raise TypeError("DynamoDB streams model failed validation, missing both new & old stream images") # noqa: ERA001,E501
    #     return values # noqa: ERA001

    @field_validator("Keys", "NewImage", "OldImage", mode="before")
    def deserialize_field(cls, value):
        return {k: _DESERIALIZER.deserialize(v) for k, v in value.items()}


class UserIdentity(BaseModel):
    type: Literal["Service"]  # noqa: VNE003, A003
    principalId: Literal["dynamodb.amazonaws.com"]


class DynamoDBStreamRecordModel(BaseModel):
    eventID: str
    eventName: Literal["INSERT", "MODIFY", "REMOVE"]
    eventVersion: float
    eventSource: Literal["aws:dynamodb"]
    awsRegion: str
    eventSourceARN: str
    dynamodb: DynamoDBStreamChangedRecordModel
    userIdentity: UserIdentity | None = None


class DynamoDBStreamModel(BaseModel):
    Records: list[DynamoDBStreamRecordModel]
