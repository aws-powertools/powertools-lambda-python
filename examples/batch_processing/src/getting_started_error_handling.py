from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = BatchProcessor(event_type=EventType.SQS)
tracer = Tracer()
logger = Logger()


class InvalidPayload(Exception):
    ...


@tracer.capture_method
def record_handler(record: SQSRecord):
    payload: str = record.body
    logger.info(payload)
    if not payload:
        raise InvalidPayload("Payload does not contain minimum information to be processed.")  # (1)!


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    return process_partial_response(  # (2)!
        event=event,
        record_handler=record_handler,
        processor=processor,
        context=context,
    )
