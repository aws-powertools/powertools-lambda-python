import json

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = BatchProcessor(event_type=EventType.DynamoDBStreams)
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: DynamoDBRecord):
    if record.dynamodb and record.dynamodb.new_image:
        logger.info(record.dynamodb.new_image)
        message = record.dynamodb.new_image.get("Message")
        if message:
            payload: dict = json.loads(message)
            logger.info(payload)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    batch = event["Records"]
    with processor(records=batch, handler=record_handler):
        processed_messages = processor.process()  # kick off processing, return list[tuple]
        logger.info(f"Processed ${len(processed_messages)} messages")

    return processor.response()
