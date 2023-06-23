import json

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    ExceptionInfo,
    FailureResponse,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext


class MyProcessor(BatchProcessor):
    def failure_handler(self, record: SQSRecord, exception: ExceptionInfo) -> FailureResponse:
        metrics.add_metric(name="BatchRecordFailures", unit=MetricUnit.Count, value=1)
        return super().failure_handler(record, exception)


processor = MyProcessor(event_type=EventType.SQS)
metrics = Metrics(namespace="test")
logger = Logger()
tracer = Tracer()


@tracer.capture_method
def record_handler(record: SQSRecord):
    payload: str = record.body
    if payload:
        item: dict = json.loads(payload)
        logger.info(item)


@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context: LambdaContext):
    return process_partial_response(event=event, record_handler=record_handler, processor=processor, context=context)
