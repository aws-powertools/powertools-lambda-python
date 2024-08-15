# ruff: noqa: FA100
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Type, Union

from pydantic import BaseModel, field_validator

from aws_lambda_powertools.shared.dynamodb_deserializer import TypeDeserializer

_DESERIALIZER = TypeDeserializer()


class DynamoDBStreamChangedRecordModel(BaseModel):
    ApproximateCreationDateTime: Optional[datetime] = None
    Keys: Dict[str, Any]
    NewImage: Optional[Union[Dict[str, Any], Type[BaseModel], BaseModel]] = None
    OldImage: Optional[Union[Dict[str, Any], Type[BaseModel], BaseModel]] = None
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
    userIdentity: Optional[UserIdentity] = None


class DynamoDBStreamModel(BaseModel):
    Records: List[DynamoDBStreamRecordModel]
