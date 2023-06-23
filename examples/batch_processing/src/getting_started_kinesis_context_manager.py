from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType
from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import (
    KinesisStreamRecord,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = BatchProcessor(event_type=EventType.KinesisDataStreams)
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: KinesisStreamRecord):
    logger.info(record.kinesis.data_as_text)
    payload: dict = record.kinesis.data_as_json()
    logger.info(payload)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    batch = event["Records"]
    with processor(records=batch, handler=record_handler):
        processed_messages = processor.process()  # kick off processing, return list[tuple]
        logger.info(f"Processed ${len(processed_messages)} messages")

    return processor.response()
