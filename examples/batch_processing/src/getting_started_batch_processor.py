from aws_lambda_powertools.utilities.batch import EventType, batch_processor, BatchProcessor
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext


def record_handler(record: SQSRecord):
    """
    Process here each record
    """
    payload: str = record.body
    if not payload:
        raise ValueError
    # code code code


processor = BatchProcessor(event_type=EventType.SQS)


@batch_processor(record_handler=record_handler, processor=processor)
def lambda_handler(event, context: LambdaContext):
    return processor.response()
