import logging
from typing import Optional, Set

from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, ExceptionInfo, FailureResponse
from aws_lambda_powertools.utilities.batch.exceptions import (
    SQSFifoCircuitBreakerError,
    SQSFifoMessageGroupCircuitBreakerError,
)
from aws_lambda_powertools.utilities.batch.types import BatchSqsTypeModel

logger = logging.getLogger(__name__)


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

    group_circuit_breaker_exc = (
        SQSFifoMessageGroupCircuitBreakerError,
        SQSFifoMessageGroupCircuitBreakerError("A previous record from this message group failed processing"),
        None,
    )

    def __init__(self, model: Optional["BatchSqsTypeModel"] = None, skip_group_on_error: bool = False):
        """
        Initialize the SqsFifoProcessor.

        Parameters
        ----------
        model: Optional["BatchSqsTypeModel"]
            An optional model for batch processing.
        skip_group_on_error: bool
            Determines whether to exclusively skip messages from the MessageGroupID that encountered processing failures
            Default is False.

        """
        self._skip_group_on_error: bool = skip_group_on_error
        self._current_group_id = None
        self._failed_group_ids: Set[str] = set()
        super().__init__(EventType.SQS, model)

    def _process_record(self, record):
        self._current_group_id = record.get("attributes", {}).get("MessageGroupId")

        # Short-circuits the process if:
        #     - There are failed messages, OR
        #     - The `skip_group_on_error` option is on, and the current message is part of a failed group.
        fail_entire_batch = bool(self.fail_messages) and not self._skip_group_on_error
        fail_group_id = self._skip_group_on_error and self._current_group_id in self._failed_group_ids
        if fail_entire_batch or fail_group_id:
            return self.failure_handler(
                record=self._to_batch_type(record, event_type=self.event_type, model=self.model),
                exception=self.group_circuit_breaker_exc if self._skip_group_on_error else self.circuit_breaker_exc,
            )

        return super()._process_record(record)

    def failure_handler(self, record, exception: ExceptionInfo) -> FailureResponse:
        # If we are failing a message and the `skip_group_on_error` is on, we store the failed group ID
        # This way, future messages with the same group ID will be failed automatically.
        if self._skip_group_on_error and self._current_group_id:
            self._failed_group_ids.add(self._current_group_id)

        return super().failure_handler(record, exception)

    def _clean(self):
        self._failed_group_ids.clear()
        self._current_group_id = None

        super()._clean()

    async def _async_process_record(self, record: dict):
        raise NotImplementedError()
