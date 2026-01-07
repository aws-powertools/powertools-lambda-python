from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, process_partial_response
from aws_lambda_powertools.utilities.batch.types import PartialItemFailureResponse
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = BatchProcessor(event_type=EventType.SQS)


def record_handler(record: SQSRecord) -> None:
    # Process each record
    payload = record.body  # noqa: F841
    # Your processing logic here


def lambda_handler(event: dict, context: LambdaContext) -> PartialItemFailureResponse:
    return process_partial_response(event=event, record_handler=record_handler, processor=processor, context=context)
