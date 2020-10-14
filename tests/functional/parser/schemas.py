from typing import Dict, List, Optional

from pydantic import BaseModel
from typing_extensions import Literal

from aws_lambda_powertools.utilities.parser.models import (
    DynamoDBStreamChangedRecordModel,
    DynamoDBStreamModel,
    DynamoDBStreamRecordModel,
    EventBridgeModel,
    SqsModel,
    SqsRecordModel,
)


class MyDynamoBusiness(BaseModel):
    Message: Dict[Literal["S"], str]
    Id: Dict[Literal["N"], int]


class MyDynamoScheme(DynamoDBStreamChangedRecordModel):
    NewImage: Optional[MyDynamoBusiness]
    OldImage: Optional[MyDynamoBusiness]


class MyDynamoDBStreamRecordModel(DynamoDBStreamRecordModel):
    dynamodb: MyDynamoScheme


class MyAdvancedDynamoBusiness(DynamoDBStreamModel):
    Records: List[MyDynamoDBStreamRecordModel]


class MyEventbridgeBusiness(BaseModel):
    instance_id: str
    state: str


class MyAdvancedEventbridgeBusiness(EventBridgeModel):
    detail: MyEventbridgeBusiness


class MySqsBusiness(BaseModel):
    message: str
    username: str


class MyAdvancedSqsRecordModel(SqsRecordModel):
    body: str


class MyAdvancedSqsBusiness(SqsModel):
    Records: List[MyAdvancedSqsRecordModel]
