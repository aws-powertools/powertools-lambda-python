from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import SqsFifoPartialProcessor
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = SqsFifoPartialProcessor()
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: SQSRecord):
    ...


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    batch = event["Records"]
    with processor(records=batch, handler=record_handler):
        processor.process()  # kick off processing, return List[Tuple]

    return processor.response()
