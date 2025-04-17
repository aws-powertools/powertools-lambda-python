"""
Batch processing utilities
!!! abstract "Usage Documentation"
    [`Batch processing`](../../utilities/batch.md)
"""

from __future__ import annotations

import asyncio
import copy
import inspect
import logging
import os
import sys
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Tuple, Union, overload

from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.utilities.batch.exceptions import (
    BatchProcessingError,
    ExceptionInfo,
)
from aws_lambda_powertools.utilities.batch.types import BatchTypeModels
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
)
from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import (
    KinesisStreamRecord,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.batch.types import (
        PartialItemFailureResponse,
        PartialItemFailures,
    )
    from aws_lambda_powertools.utilities.typing import LambdaContext

logger = logging.getLogger(__name__)


class EventType(Enum):
    SQS = "SQS"
    KinesisDataStreams = "KinesisDataStreams"
    DynamoDBStreams = "DynamoDBStreams"


# When using processor with default arguments, records will carry EventSourceDataClassTypes
# and depending on what EventType it's passed it'll correctly map to the right record
# When using Pydantic Models, it'll accept any subclass from SQS, DynamoDB and Kinesis
EventSourceDataClassTypes = Union[SQSRecord, KinesisStreamRecord, DynamoDBRecord]
BatchEventTypes = Union[EventSourceDataClassTypes, BatchTypeModels]
SuccessResponse = Tuple[str, Any, BatchEventTypes]
FailureResponse = Tuple[str, str, BatchEventTypes]


class BasePartialProcessor(ABC):
    """
    Abstract class for batch processors.
    """

    lambda_context: LambdaContext

    def __init__(self):
        self.success_messages: list[BatchEventTypes] = []
        self.fail_messages: list[BatchEventTypes] = []
        self.exceptions: list[ExceptionInfo] = []

    @abstractmethod
    def _prepare(self):
        """
        Prepare context manager.
        """
        raise NotImplementedError()

    @abstractmethod
    def _clean(self):
        """
        Clear context manager.
        """
        raise NotImplementedError()

    @abstractmethod
    def _process_record(self, record: dict):
        """
        Process record with handler.
        """
        raise NotImplementedError()

    def process(self) -> list[tuple]:
        """
        Call instance's handler for each record.
        """
        return [self._process_record(record) for record in self.records]

    @abstractmethod
    async def _async_process_record(self, record: dict):
        """
        Async process record with handler.
        """
        raise NotImplementedError()

    def async_process(self) -> list[tuple]:
        """
        Async call instance's handler for each record.

        Note
        ----

        We keep the outer function synchronous to prevent making Lambda handler async, so to not impact
        customers' existing middlewares. Instead, we create an async closure to handle asynchrony.

        We also handle edge cases like Lambda container thaw by getting an existing or creating an event loop.

        See: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html#runtimes-lifecycle-shutdown
        """

        async def async_process_closure():
            return list(await asyncio.gather(*[self._async_process_record(record) for record in self.records]))

        # WARNING
        # Do not use "asyncio.run(async_process())" due to Lambda container thaws/freeze, otherwise we might get "Event Loop is closed" # noqa: E501
        # Instead, get_event_loop() can also create one if a previous was erroneously closed
        # Mangum library does this as well. It's battle tested with other popular async-only frameworks like FastAPI
        # https://github.com/jordaneremieff/mangum/discussions/256#discussioncomment-2638946
        # https://github.com/jordaneremieff/mangum/blob/b85cd4a97f8ddd56094ccc540ca7156c76081745/mangum/protocols/http.py#L44

        # Let's prime the coroutine and decide
        # whether we create an event loop (Lambda) or schedule it as usual (non-Lambda)
        coro = async_process_closure()
        if os.getenv(constants.LAMBDA_TASK_ROOT_ENV):
            loop = asyncio.get_event_loop()  # NOTE: this might return an error starting in Python 3.12 in a few years
            task_instance = loop.create_task(coro)
            return loop.run_until_complete(task_instance)

        # Non-Lambda environment, run coroutine as usual
        return asyncio.run(coro)

    def __enter__(self):
        self._prepare()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._clean()

    def __call__(self, records: list[dict], handler: Callable, lambda_context: LambdaContext | None = None):
        """
        Set instance attributes before execution

        Parameters
        ----------
        records: list[dict]
            List with objects to be processed.
        handler: Callable
            Callable to process "records" entries.
        """
        self.records = records
        self.handler = handler

        # NOTE: If a record handler has `lambda_context` parameter in its function signature, we inject it.
        # This is the earliest we can inspect for signature to prevent impacting performance.
        #
        #   Mechanism:
        #
        #   1. When using the `@batch_processor` decorator, this happens automatically.
        #   2. When using the context manager, customers have to include `lambda_context` param.
        #
        #   Scenario: Injects Lambda context
        #
        #   def record_handler(record, lambda_context): ... # noqa: ERA001
        #   with processor(records=batch, handler=record_handler, lambda_context=context): ... # noqa: ERA001
        #
        #   Scenario: Does NOT inject Lambda context (default)
        #
        #   def record_handler(record): pass # noqa: ERA001
        #   with processor(records=batch, handler=record_handler): ... # noqa: ERA001
        #
        if lambda_context is None:
            self._handler_accepts_lambda_context = False
        else:
            self.lambda_context = lambda_context
            self._handler_accepts_lambda_context = "lambda_context" in inspect.signature(self.handler).parameters

        return self

    def success_handler(self, record, result: Any) -> SuccessResponse:
        """
        Keeps track of batch records that were processed successfully

        Parameters
        ----------
        record: Any
            record that succeeded processing
        result: Any
            result from record handler

        Returns
        -------
        SuccessResponse
            "success", result, original record
        """
        entry = ("success", result, record)
        self.success_messages.append(record)
        return entry

    def failure_handler(self, record, exception: ExceptionInfo) -> FailureResponse:
        """
        Keeps track of batch records that failed processing

        Parameters
        ----------
        record: Any
            record that failed processing
        exception: ExceptionInfo
            Exception information containing type, value, and traceback (sys.exc_info())

        Returns
        -------
        FailureResponse
            "fail", exceptions args, original record
        """
        exception_string = f"{exception[0]}:{exception[1]}"
        entry = ("fail", exception_string, record)
        logger.debug(f"Record processing exception: {exception_string}")
        self.exceptions.append(exception)
        self.fail_messages.append(record)
        return entry


class BasePartialBatchProcessor(BasePartialProcessor):  # noqa
    DEFAULT_RESPONSE: PartialItemFailureResponse = {"batchItemFailures": []}

    def __init__(
        self,
        event_type: EventType,
        model: BatchTypeModels | None = None,
        raise_on_entire_batch_failure: bool = True,
    ):
        """Process batch and partially report failed items

        Parameters
        ----------
        event_type: EventType
            Whether this is a SQS, DynamoDB Streams, or Kinesis Data Stream event
        model: BatchTypeModels | None
            Parser's data model using either SqsRecordModel, DynamoDBStreamRecordModel, KinesisDataStreamRecord
        raise_on_entire_batch_failure: bool
            Raise an exception when the entire batch has failed processing.
            When set to False, partial failures are reported in the response

        Exceptions
        ----------
        BatchProcessingError
            Raised when the entire batch has failed processing
        """
        self.event_type = event_type
        self.model = model
        self.raise_on_entire_batch_failure = raise_on_entire_batch_failure
        self.batch_response: PartialItemFailureResponse = copy.deepcopy(self.DEFAULT_RESPONSE)
        self._COLLECTOR_MAPPING = {
            EventType.SQS: self._collect_sqs_failures,
            EventType.KinesisDataStreams: self._collect_kinesis_failures,
            EventType.DynamoDBStreams: self._collect_dynamodb_failures,
        }
        self._DATA_CLASS_MAPPING = {
            EventType.SQS: SQSRecord,
            EventType.KinesisDataStreams: KinesisStreamRecord,
            EventType.DynamoDBStreams: DynamoDBRecord,
        }

        super().__init__()

    def response(self) -> PartialItemFailureResponse:
        """Batch items that failed processing, if any"""
        return self.batch_response

    def _prepare(self):
        """
        Remove results from previous execution.
        """
        self.success_messages.clear()
        self.fail_messages.clear()
        self.exceptions.clear()
        self.batch_response = copy.deepcopy(self.DEFAULT_RESPONSE)

    def _clean(self):
        """
        Report messages to be deleted in case of partial failure.
        """

        if not self._has_messages_to_report():
            return

        if self._entire_batch_failed() and self.raise_on_entire_batch_failure:
            raise BatchProcessingError(
                msg=f"All records failed processing. {len(self.exceptions)} individual errors logged separately below.",
                child_exceptions=self.exceptions,
            )

        messages = self._get_messages_to_report()
        self.batch_response = {"batchItemFailures": messages}

    def _has_messages_to_report(self) -> bool:
        if self.fail_messages:
            return True

        logger.debug(f"All {len(self.success_messages)} records successfully processed")
        return False

    def _entire_batch_failed(self) -> bool:
        return len(self.exceptions) == len(self.records)

    def _get_messages_to_report(self) -> list[PartialItemFailures]:
        """
        Format messages to use in batch deletion
        """
        return self._COLLECTOR_MAPPING[self.event_type]()

    # Event Source Data Classes follow python idioms for fields
    # while Parser/Pydantic follows the event field names to the latter
    def _collect_sqs_failures(self):
        failures = []
        for msg in self.fail_messages:
            # If a message failed due to model validation (e.g., poison pill)
            # we convert to an event source data class...but self.model is still true
            # therefore, we do an additional check on whether the failed message is still a model
            # see https://github.com/aws-powertools/powertools-lambda-python/issues/2091
            if self.model and getattr(msg, "model_validate", None):
                msg_id = msg.messageId
            else:
                msg_id = msg.message_id
            failures.append({"itemIdentifier": msg_id})
        return failures

    def _collect_kinesis_failures(self):
        failures = []
        for msg in self.fail_messages:
            # # see https://github.com/aws-powertools/powertools-lambda-python/issues/2091
            if self.model and getattr(msg, "model_validate", None):
                msg_id = msg.kinesis.sequenceNumber
            else:
                msg_id = msg.kinesis.sequence_number
            failures.append({"itemIdentifier": msg_id})
        return failures

    def _collect_dynamodb_failures(self):
        failures = []
        for msg in self.fail_messages:
            # see https://github.com/aws-powertools/powertools-lambda-python/issues/2091
            if self.model and getattr(msg, "model_validate", None):
                msg_id = msg.dynamodb.SequenceNumber
            else:
                msg_id = msg.dynamodb.sequence_number
            failures.append({"itemIdentifier": msg_id})
        return failures

    @overload
    def _to_batch_type(
        self,
        record: dict,
        event_type: EventType,
        model: BatchTypeModels,
    ) -> BatchTypeModels: ...  # pragma: no cover

    @overload
    def _to_batch_type(self, record: dict, event_type: EventType) -> EventSourceDataClassTypes: ...  # pragma: no cover

    def _to_batch_type(self, record: dict, event_type: EventType, model: BatchTypeModels | None = None):
        if model is not None:
            # If a model is provided, we assume Pydantic is installed and we need to disable v2 warnings
            return model.model_validate(record)
        return self._DATA_CLASS_MAPPING[event_type](record)

    def _register_model_validation_error_record(self, record: dict):
        """Convert and register failure due to poison pills where model failed validation early"""
        # Parser will fail validation if record is a poison pill (malformed input)
        # this means we can't collect the message id if we try transforming again
        # so we convert into to the equivalent batch type model (e.g., SQS, Kinesis, DynamoDB Stream)
        # and downstream we can correctly collect the correct message id identifier and make the failed record available
        # see https://github.com/aws-powertools/powertools-lambda-python/issues/2091
        logger.debug("Record cannot be converted to customer's model; converting without model")
        failed_record: EventSourceDataClassTypes = self._to_batch_type(record=record, event_type=self.event_type)
        return self.failure_handler(record=failed_record, exception=sys.exc_info())


class BatchProcessor(BasePartialBatchProcessor):  # Keep old name for compatibility
    """Process native partial responses from SQS, Kinesis Data Streams, and DynamoDB.

    Example
    -------

    ## Process batch triggered by SQS

    ```python
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
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
    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context: LambdaContext):
        return processor.response()
    ```

    ## Process batch triggered by Kinesis Data Streams

    ```python
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
    from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import KinesisStreamRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = BatchProcessor(event_type=EventType.KinesisDataStreams)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: KinesisStreamRecord):
        logger.info(record.kinesis.data_as_text)
        payload: dict = record.kinesis.data_as_json()
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context: LambdaContext):
        return processor.response()
    ```

    ## Process batch triggered by DynamoDB Data Streams

    ```python
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
    from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = BatchProcessor(event_type=EventType.DynamoDBStreams)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: DynamoDBRecord):
        logger.info(record.dynamodb.new_image)
        payload: dict = json.loads(record.dynamodb.new_image.get("item"))
        # alternatively:
        # changes: dict[str, Any] = record.dynamodb.new_image  # noqa: ERA001
        # payload = change.get("Message") -> "<payload>"
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    def lambda_handler(event, context: LambdaContext):
        batch = event["Records"]
        with processor(records=batch, processor=processor):
            processed_messages = processor.process() # kick off processing, return list[tuple]

        return processor.response()
    ```


    Raises
    ------
    BatchProcessingError
        When all batch records fail processing and raise_on_entire_batch_failure is True

    Limitations
    -----------
    * Async record handler not supported, use AsyncBatchProcessor instead.
    """

    async def _async_process_record(self, record: dict):
        raise NotImplementedError()

    def _process_record(self, record: dict) -> SuccessResponse | FailureResponse:
        """
        Process a record with instance's handler

        Parameters
        ----------
        record: dict
            A batch record to be processed.
        """
        data: BatchTypeModels | None = None
        try:
            data = self._to_batch_type(record=record, event_type=self.event_type, model=self.model)
            if self._handler_accepts_lambda_context:
                result = self.handler(record=data, lambda_context=self.lambda_context)
            else:
                result = self.handler(record=data)

            return self.success_handler(record=record, result=result)
        except Exception as exc:
            # NOTE: Pydantic is an optional dependency, but when used and a poison pill scenario happens
            # we need to handle that exception differently.
            # We check for a public attr in validation errors coming from Pydantic exceptions (subclass or not)
            # and we compare if it's coming from the same model that trigger the exception in the first place

            # Pydantic v1 raises a ValidationError with ErrorWrappers and store the model instance in a class variable.
            # Pydantic v2 simplifies this by adding a title variable to store the model name directly.
            model = getattr(exc, "model", None) or getattr(exc, "title", None)
            model_name = getattr(self.model, "__name__", None)

            if model in (self.model, model_name):
                return self._register_model_validation_error_record(record)

            return self.failure_handler(record=data, exception=sys.exc_info())


class AsyncBatchProcessor(BasePartialBatchProcessor):
    """Process native partial responses from SQS, Kinesis Data Streams, and DynamoDB asynchronously.

    Example
    -------

    ## Process batch triggered by SQS

    ```python
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
    from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = BatchProcessor(event_type=EventType.SQS)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    async def record_handler(record: SQSRecord):
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

    ## Process batch triggered by Kinesis Data Streams

    ```python
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
    from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import KinesisStreamRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = BatchProcessor(event_type=EventType.KinesisDataStreams)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    async def record_handler(record: KinesisStreamRecord):
        logger.info(record.kinesis.data_as_text)
        payload: dict = record.kinesis.data_as_json()
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context: LambdaContext):
        return processor.response()
    ```

    ## Process batch triggered by DynamoDB Data Streams

    ```python
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
    from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = BatchProcessor(event_type=EventType.DynamoDBStreams)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    async def record_handler(record: DynamoDBRecord):
        logger.info(record.dynamodb.new_image)
        payload: dict = json.loads(record.dynamodb.new_image.get("item"))
        # alternatively:
        # changes: dict[str, Any] = record.dynamodb.new_image  # noqa: ERA001
        # payload = change.get("Message") -> "<payload>"
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    def lambda_handler(event, context: LambdaContext):
        batch = event["Records"]
        with processor(records=batch, processor=processor):
            processed_messages = processor.process() # kick off processing, return list[tuple]

        return processor.response()
    ```


    Raises
    ------
    BatchProcessingError
        When all batch records fail processing and raise_on_entire_batch_failure is True

    Limitations
    -----------
    * Sync record handler not supported, use BatchProcessor instead.
    """

    def _process_record(self, record: dict):
        raise NotImplementedError()

    async def _async_process_record(self, record: dict) -> SuccessResponse | FailureResponse:
        """
        Process a record with instance's handler

        Parameters
        ----------
        record: dict
            A batch record to be processed.
        """
        data: BatchTypeModels | None = None
        try:
            data = self._to_batch_type(record=record, event_type=self.event_type, model=self.model)
            if self._handler_accepts_lambda_context:
                result = await self.handler(record=data, lambda_context=self.lambda_context)
            else:
                result = await self.handler(record=data)

            return self.success_handler(record=record, result=result)
        except Exception as exc:
            # NOTE: Pydantic is an optional dependency, but when used and a poison pill scenario happens
            # we need to handle that exception differently.
            # We check for a public attr in validation errors coming from Pydantic exceptions (subclass or not)
            # and we compare if it's coming from the same model that trigger the exception in the first place

            # Pydantic v1 raises a ValidationError with ErrorWrappers and store the model instance in a class variable.
            # Pydantic v2 simplifies this by adding a title variable to store the model name directly.
            model = getattr(exc, "model", None) or getattr(exc, "title", None)
            model_name = getattr(self.model, "__name__", None)

            if model in (self.model, model_name):
                return self._register_model_validation_error_record(record)

            return self.failure_handler(record=data, exception=sys.exc_info())
