import json

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
from aws_lambda_powertools.utilities.parser import BaseModel, validator
from aws_lambda_powertools.utilities.parser.models import SqsRecordModel
from aws_lambda_powertools.utilities.typing import LambdaContext


class Order(BaseModel):
    item: dict


class OrderSqsRecord(SqsRecordModel):
    body: Order

    # auto transform json string
    # so Pydantic can auto-initialize nested Order model
    @validator("body", pre=True)
    def transform_body_to_dict(cls, value: str):
        return json.loads(value)


processor = BatchProcessor(event_type=EventType.SQS, model=OrderSqsRecord)
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: OrderSqsRecord):
    return record.body.item


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@batch_processor(record_handler=record_handler, processor=processor)
def lambda_handler(event, context: LambdaContext):
    return processor.response()
