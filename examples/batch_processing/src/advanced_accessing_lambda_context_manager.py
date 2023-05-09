from typing import Optional

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = BatchProcessor(event_type=EventType.SQS)
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: SQSRecord, lambda_context: Optional[LambdaContext] = None):
    if lambda_context is not None:
        remaining_time = lambda_context.get_remaining_time_in_millis()
        logger.info(remaining_time)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    batch = event["Records"]
    with processor(records=batch, handler=record_handler, lambda_context=context):
        result = processor.process()

    return result
