from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import (
    KinesisStreamRecord,
    extract_cloudwatch_logs_from_record,
)

logger = Logger()

processor = BatchProcessor(event_type=EventType.KinesisDataStreams)


def record_handler(record: KinesisStreamRecord):
    log = extract_cloudwatch_logs_from_record(record)
    logger.info(f"Message type: {log.message_type}")
    return log.message_type == "DATA_MESSAGE"


def lambda_handler(event, context):
    return process_partial_response(
        event=event,
        record_handler=record_handler,
        processor=processor,
        context=context,
    )
