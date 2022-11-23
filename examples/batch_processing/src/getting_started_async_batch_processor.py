from aws_lambda_powertools.utilities.batch import async_batch_processor, EventType, AsyncBatchProcessor
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext


async def async_record_handler(record: SQSRecord):
    """
    Process here each record
    """
    payload: str = record.body
    if not payload:
        raise ValueError
    # code code code


processor = AsyncBatchProcessor(event_type=EventType.SQS)


@async_batch_processor(record_handler=async_record_handler, processor=processor)
async def lambda_handler(event, context: LambdaContext):
    return processor.response()
