import json
from typing import Dict, Optional

from pydantic import field_validator

from aws_lambda_powertools.utilities.parser import BaseModel
from aws_lambda_powertools.utilities.parser.models import (
    DynamoDBStreamChangedRecordModel,
    DynamoDBStreamRecordModel,
    KinesisDataStreamRecord,
    KinesisDataStreamRecordPayload,
    SqsRecordModel,
)
from aws_lambda_powertools.utilities.parser.types import Json, Literal


class Order(BaseModel):
    item: dict


class OrderSqs(SqsRecordModel):
    body: Json[Order]


class OrderKinesisPayloadRecord(KinesisDataStreamRecordPayload):
    data: Json[Order]


class OrderKinesisRecord(KinesisDataStreamRecord):
    kinesis: OrderKinesisPayloadRecord


class OrderDynamoDB(BaseModel):
    Message: Order

    # auto transform json string
    # so Pydantic can auto-initialize nested Order model
    @field_validator("Message", mode="before")
    def transform_message_to_dict(cls, value: Dict[Literal["S"], str]):
        try:
            return json.loads(value["S"])
        except TypeError:
            raise ValueError


class OrderDynamoDBChangeRecord(DynamoDBStreamChangedRecordModel):
    NewImage: Optional[OrderDynamoDB] = None
    OldImage: Optional[OrderDynamoDB] = None


class OrderDynamoDBRecord(DynamoDBStreamRecordModel):
    dynamodb: OrderDynamoDBChangeRecord
