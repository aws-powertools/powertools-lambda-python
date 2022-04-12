import json

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = BatchProcessor(event_type=EventType.DynamoDBStreams)
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: DynamoDBRecord):
    logger.info(record.dynamodb.new_image)
    payload: dict = json.loads(record.dynamodb.new_image.get("item").s_value)
    # alternatively:
    # changes: Dict[str, dynamo_db_stream_event.AttributeValue] = record.dynamodb.new_image
    # payload = change.get("Message").raw_event -> {"S": "<payload>"}
    ...


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    batch = event["Records"]
    with processor(records=batch, handler=record_handler):
        processed_messages = processor.process()  # kick off processing, return list[tuple]

    return processor.response()
