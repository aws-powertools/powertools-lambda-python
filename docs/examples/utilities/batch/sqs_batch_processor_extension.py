import json

from aws_lambda_powertools import Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    ExceptionInfo,
    FailureResponse,
    batch_processor,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()


class MyProcessor(BatchProcessor):
    def failure_handler(self, record: SQSRecord, exception: ExceptionInfo) -> FailureResponse:
        metrics.add_metric(name="BatchRecordFailures", unit=MetricUnit.Count, value=1)
        return super().failure_handler(record, exception)


processor = MyProcessor(event_type=EventType.SQS)
metrics = Metrics(namespace="test")


@tracer.capture_method
def record_handler(record: SQSRecord):
    payload: str = record.body
    if payload:
        item: dict = json.loads(payload)
    ...


@metrics.log_metrics(capture_cold_start_metric=True)
@batch_processor(record_handler=record_handler, processor=processor)
def lambda_handler(event, context: LambdaContext):
    return processor.response()
