from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.parser import BaseModel
from aws_lambda_powertools.utilities.parser.models import SqsRecordModel
from aws_lambda_powertools.utilities.parser.types import Json
from aws_lambda_powertools.utilities.typing import LambdaContext


class Order(BaseModel):
    item: dict


class OrderSqsRecord(SqsRecordModel):
    body: Json[Order]  # deserialize order data from JSON string


processor = BatchProcessor(event_type=EventType.SQS, model=OrderSqsRecord)
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: OrderSqsRecord):
    logger.info(record.body.item)
    return record.body.item


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    return process_partial_response(event=event, record_handler=record_handler, processor=processor, context=context)
