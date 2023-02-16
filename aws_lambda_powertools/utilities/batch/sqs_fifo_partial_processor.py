import sys
from typing import List, Optional, Tuple, Type

from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType
from aws_lambda_powertools.utilities.parser.models import SqsRecordModel

#
# type specifics
#
has_pydantic = "pydantic" in sys.modules

# For IntelliSense and Mypy to work, we need to account for possible SQS subclasses
# We need them as subclasses as we must access their message ID or sequence number metadata via dot notation
if has_pydantic:
    BatchTypeModels = Optional[Type[SqsRecordModel]]


class SQSFifoCircuitBreakerError(Exception):
    """
    Signals a record not processed due to the SQS FIFO processing being interrupted
    """

    pass


class SQSFifoPartialProcessor(BatchProcessor):
    """Specialized BatchProcessor subclass that handles FIFO SQS batch records.

    As soon as the processing of the first record fails, the remaining records
    are marked as failed without processing, and returned as native partial responses.

    Example
    _______

    ## Process batch triggered by a FIFO SQS

    ```python
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import SQSFifoPartialProcessor, EventType, batch_processor
    from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = SQSFifoPartialProcessor()
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

    circuitBreakerError = SQSFifoCircuitBreakerError("A previous record failed processing.")

    def __init__(self, model: Optional["BatchTypeModels"] = None):
        super().__init__(EventType.SQS, model)

    def process(self) -> List[Tuple]:
        result: List[Tuple] = []

        for i, record in enumerate(self.records):
            """
            If we have failed messages, it means that the last message failed.
            We then short circuit the process, failing the remaining messages
            """
            if self.fail_messages:
                return self._short_circuit_processing(i, result)

            """
            Otherwise, process the message normally
            """
            result.append(self._process_record(record))

        return result

    def _short_circuit_processing(self, first_failure_index: int, result: List[Tuple]) -> List[Tuple]:
        remaining_records = self.records[first_failure_index:]
        for remaining_record in remaining_records:
            data = self._to_batch_type(record=remaining_record, event_type=self.event_type, model=self.model)
            result.append(
                self.failure_handler(
                    record=data, exception=(type(self.circuitBreakerError), self.circuitBreakerError, None)
                )
            )
        return result

    async def _async_process_record(self, record: dict):
        raise NotImplementedError()
