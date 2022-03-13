import json

from pydantic import BaseModel

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
from aws_lambda_powertools.utilities.parser import BaseModel, validator
from aws_lambda_powertools.utilities.parser.models import KinesisDataStreamRecord, KinesisDataStreamRecordPayload
from aws_lambda_powertools.utilities.typing import LambdaContext


class Order(BaseModel):
    item: dict


class OrderKinesisPayloadRecord(KinesisDataStreamRecordPayload):
    data: Order

    # auto transform json string
    # so Pydantic can auto-initialize nested Order model
    @validator("data", pre=True)
    def transform_message_to_dict(cls, value: str):
        # Powertools KinesisDataStreamRecordPayload already decodes b64 to str here
        return json.loads(value)


class OrderKinesisRecord(KinesisDataStreamRecord):
    kinesis: OrderKinesisPayloadRecord


processor = BatchProcessor(event_type=EventType.KinesisDataStreams, model=OrderKinesisRecord)
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: OrderKinesisRecord):
    return record.kinesis.data.item


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@batch_processor(record_handler=record_handler, processor=processor)
def lambda_handler(event, context: LambdaContext):
    return processor.response()
