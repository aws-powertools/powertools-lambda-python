from typing import Dict, List, Optional

from pydantic import BaseModel
from typing_extensions import Literal

from aws_lambda_powertools.utilities.parser.schemas import (
    DynamoDBStreamChangedRecordSchema,
    DynamoDBStreamRecordSchema,
    DynamoDBStreamSchema,
    EventBridgeSchema,
    SqsRecordSchema,
    SqsSchema,
)


class MyDynamoBusiness(BaseModel):
    Message: Dict[Literal["S"], str]
    Id: Dict[Literal["N"], int]


class MyDynamoScheme(DynamoDBStreamChangedRecordSchema):
    NewImage: Optional[MyDynamoBusiness]
    OldImage: Optional[MyDynamoBusiness]


class MyDynamoDBStreamRecordSchema(DynamoDBStreamRecordSchema):
    dynamodb: MyDynamoScheme


class MyAdvancedDynamoBusiness(DynamoDBStreamSchema):
    Records: List[MyDynamoDBStreamRecordSchema]


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
