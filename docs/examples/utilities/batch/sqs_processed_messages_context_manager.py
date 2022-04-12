import json
from typing import Any, List, Literal, Union

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, FailureResponse, SuccessResponse
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = BatchProcessor(event_type=EventType.SQS)
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: SQSRecord):
    payload: str = record.body
    if payload:
        item: dict = json.loads(payload)
    ...


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    batch = event["Records"]
    with processor(records=batch, handler=record_handler):
        processed_messages: List[Union[SuccessResponse, FailureResponse]] = processor.process()

    for message in processed_messages:
        status: Union[Literal["success"], Literal["fail"]] = message[0]
        result: Any = message[1]
        record: SQSRecord = message[2]

    return processor.response()
