from typing import List, Optional, Tuple

from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType
from aws_lambda_powertools.utilities.batch.types import BatchSqsTypeModel


class SQSFifoCircuitBreakerError(Exception):
    """
    Signals a record not processed due to the SQS FIFO processing being interrupted
    """

    pass


class SqsFifoPartialProcessor(BatchProcessor):
    """Process native partial responses from SQS FIFO queues.

    Stops processing records when the first record fails. The remaining records are reported as failed items.

    Example
    _______

    ## Process batch triggered by a FIFO SQS

    ```python
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import SqsFifoPartialProcessor, EventType, batch_processor
    from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = SqsFifoPartialProcessor()
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
    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context: LambdaContext):
        return processor.response()
    ```
    """

    circuit_breaker_exc = (
        SQSFifoCircuitBreakerError,
        SQSFifoCircuitBreakerError("A previous record failed processing"),
        None,
    )

    def __init__(self, model: Optional["BatchSqsTypeModel"] = None):
        super().__init__(EventType.SQS, model)

    def process(self) -> List[Tuple]:
        """
        Call instance's handler for each record. When the first failed message is detected,
        the process is short-circuited, and the remaining messages are reported as failed items.
        """
        result: List[Tuple] = []

        for i, record in enumerate(self.records):
            # If we have failed messages, it means that the last message failed.
            # We then short circuit the process, failing the remaining messages
            if self.fail_messages:
                return self._short_circuit_processing(i, result)

            # Otherwise, process the message normally
            result.append(self._process_record(record))

        return result

    def _short_circuit_processing(self, first_failure_index: int, result: List[Tuple]) -> List[Tuple]:
        """
        Starting from the first failure index, fail all the remaining messages, and append them to the result list.
        """
        remaining_records = self.records[first_failure_index:]
        for remaining_record in remaining_records:
            data = self._to_batch_type(record=remaining_record, event_type=self.event_type, model=self.model)
            result.append(self.failure_handler(record=data, exception=self.circuit_breaker_exc))
        return result

    async def _async_process_record(self, record: dict):
        raise NotImplementedError()
