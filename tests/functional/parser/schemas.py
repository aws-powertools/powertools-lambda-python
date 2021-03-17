from typing import Dict, List, Optional

from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser.models import (
    DynamoDBStreamChangedRecordModel,
    DynamoDBStreamModel,
    DynamoDBStreamRecordModel,
    EventBridgeModel,
    SnsModel,
    SnsNotificationModel,
    SnsRecordModel,
    SqsModel,
    SqsRecordModel,
)
from aws_lambda_powertools.utilities.parser.types import Literal


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


class MySnsBusiness(BaseModel):
    message: str
    username: str


class MySnsNotificationModel(SnsNotificationModel):
    Message: str


class MyAdvancedSnsRecordModel(SnsRecordModel):
    Sns: MySnsNotificationModel


class MyAdvancedSnsBusiness(SnsModel):
    Records: List[MyAdvancedSnsRecordModel]


class MyKinesisBusiness(BaseModel):
    message: str
    username: str


class MyCloudWatchBusiness(BaseModel):
    my_message: str
    user: str
