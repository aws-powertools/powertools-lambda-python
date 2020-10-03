from typing import Dict, List, Optional

from pydantic import BaseModel
from typing_extensions import Literal

from aws_lambda_powertools.utilities.advanced_parser.schemas import (
    DynamoDBSchema,
    DynamoRecordSchema,
    DynamoScheme,
    EventBridgeSchema,
    SqsRecordSchema,
    SqsSchema,
)


class MyDynamoBusiness(BaseModel):
    Message: Dict[Literal["S"], str]
    Id: Dict[Literal["N"], int]


class MyDynamoScheme(DynamoScheme):
    NewImage: Optional[MyDynamoBusiness]
    OldImage: Optional[MyDynamoBusiness]


class MyDynamoRecordSchema(DynamoRecordSchema):
    dynamodb: MyDynamoScheme


class MyAdvancedDynamoBusiness(DynamoDBSchema):
    Records: List[MyDynamoRecordSchema]


class MyEventbridgeBusiness(BaseModel):
    instance_id: str
    state: str


class MyAdvancedEventbridgeBusiness(EventBridgeSchema):
    detail: MyEventbridgeBusiness


class MySqsBusiness(BaseModel):
    message: str
    username: str


class MyAdvancedSqsRecordSchema(SqsRecordSchema):
    body: str


class MyAdvancedSqsBusiness(SqsSchema):
    Records: List[MyAdvancedSqsRecordSchema]
