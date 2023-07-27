from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = BatchProcessor(event_type=EventType.SQS)  # (1)!
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: SQSRecord):  # (2)!
    payload: str = record.json_body  # if json string data, otherwise record.body for str
    logger.info(payload)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    return process_partial_response(  # (3)!
        event=event,
        record_handler=record_handler,
        processor=processor,
        context=context,
    )
