import json
from typing import Dict, Literal, Optional

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
from aws_lambda_powertools.utilities.parser import BaseModel, validator
from aws_lambda_powertools.utilities.parser.models import DynamoDBStreamChangedRecordModel, DynamoDBStreamRecordModel
from aws_lambda_powertools.utilities.typing import LambdaContext


class Order(BaseModel):
    item: dict


class OrderDynamoDB(BaseModel):
    Message: Order

    # auto transform json string
    # so Pydantic can auto-initialize nested Order model
    @validator("Message", pre=True)
    def transform_message_to_dict(cls, value: Dict[Literal["S"], str]):
        return json.loads(value["S"])


class OrderDynamoDBChangeRecord(DynamoDBStreamChangedRecordModel):
    NewImage: Optional[OrderDynamoDB]
    OldImage: Optional[OrderDynamoDB]


class OrderDynamoDBRecord(DynamoDBStreamRecordModel):
    dynamodb: OrderDynamoDBChangeRecord


processor = BatchProcessor(event_type=EventType.DynamoDBStreams, model=OrderDynamoDBRecord)
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: OrderDynamoDBRecord):
    return record.dynamodb.NewImage.Message.item


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@batch_processor(record_handler=record_handler, processor=processor)
def lambda_handler(event, context: LambdaContext):
    return processor.response()
