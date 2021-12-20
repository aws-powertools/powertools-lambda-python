# -*- coding: utf-8 -*-

"""
Batch processing utilities
"""
import copy
import logging
import sys
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, overload

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.batch.exceptions import BatchProcessingError, ExceptionInfo
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBRecord
from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import KinesisStreamRecord
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord

logger = logging.getLogger(__name__)


class EventType(Enum):
    SQS = "SQS"
    KinesisDataStreams = "KinesisDataStreams"
    DynamoDBStreams = "DynamoDBStreams"


#
# type specifics
#
has_pydantic = "pydantic" in sys.modules

# For IntelliSense and Mypy to work, we need to account for possible SQS, Kinesis and DynamoDB subclasses
# We need them as subclasses as we must access their message ID or sequence number metadata via dot notation
if has_pydantic:
    from aws_lambda_powertools.utilities.parser.models import DynamoDBStreamRecordModel
    from aws_lambda_powertools.utilities.parser.models import KinesisDataStreamRecord as KinesisDataStreamRecordModel
    from aws_lambda_powertools.utilities.parser.models import SqsRecordModel

    BatchTypeModels = Optional[
        Union[Type[SqsRecordModel], Type[DynamoDBStreamRecordModel], Type[KinesisDataStreamRecordModel]]
    ]

# When using processor with default arguments, records will carry EventSourceDataClassTypes
# and depending on what EventType it's passed it'll correctly map to the right record
# When using Pydantic Models, it'll accept any subclass from SQS, DynamoDB and Kinesis
EventSourceDataClassTypes = Union[SQSRecord, KinesisStreamRecord, DynamoDBRecord]
BatchEventTypes = Union[EventSourceDataClassTypes, "BatchTypeModels"]
SuccessResponse = Tuple[str, Any, BatchEventTypes]
FailureResponse = Tuple[str, str, BatchEventTypes]


class BasePartialProcessor(ABC):
    """
    Abstract class for batch processors.
    """

    def __init__(self):
        self.success_messages: List[BatchEventTypes] = []
        self.fail_messages: List[BatchEventTypes] = []
        self.exceptions: List[ExceptionInfo] = []

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

    def process(self) -> List[Tuple]:
        """
        Call instance's handler for each record.
        """
        return [self._process_record(record) for record in self.records]

    def __enter__(self):
        self._prepare()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._clean()

    def __call__(self, records: List[dict], handler: Callable):
        """
        Set instance attributes before execution

        Parameters
        ----------
        records: List[dict]
            List with objects to be processed.
        handler: Callable
            Callable to process "records" entries.
        """
        self.records = records
        self.handler = handler
        return self

    def success_handler(self, record, result: Any) -> SuccessResponse:
        """
        Keeps track of batch records that were processed successfully

        Parameters
        ----------
        record: Any
            record that failed processing
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


@lambda_handler_decorator
def batch_processor(
    handler: Callable, event: Dict, context: Dict, record_handler: Callable, processor: BasePartialProcessor
):
    """
    Middleware to handle batch event processing

    Parameters
    ----------
    handler: Callable
        Lambda's handler
    event: Dict
        Lambda's Event
    context: Dict
        Lambda's Context
    record_handler: Callable
        Callable to process each record from the batch
    processor: PartialSQSProcessor
        Batch Processor to handle partial failure cases

    Examples
    --------
    **Processes Lambda's event with PartialSQSProcessor**

        >>> from aws_lambda_powertools.utilities.batch import batch_processor, PartialSQSProcessor
        >>>
        >>> def record_handler(record):
        >>>     return record["body"]
        >>>
        >>> @batch_processor(record_handler=record_handler, processor=PartialSQSProcessor())
        >>> def handler(event, context):
        >>>     return {"StatusCode": 200}

    Limitations
    -----------
    * Async batch processors

    """
    records = event["Records"]

    with processor(records, record_handler):
        processor.process()

    return handler(event, context)


class BatchProcessor(BasePartialProcessor):
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
        payload: dict = json.loads(record.dynamodb.new_image.get("item").s_value)
        # alternatively:
        # changes: Dict[str, dynamo_db_stream_event.AttributeValue] = record.dynamodb.new_image  # noqa: E800
        # payload = change.get("Message").raw_event -> {"S": "<payload>"}
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
        When all batch records fail processing
    """

    DEFAULT_RESPONSE: Dict[str, List[Optional[dict]]] = {"batchItemFailures": []}

    def __init__(self, event_type: EventType, model: Optional["BatchTypeModels"] = None):
        """Process batch and partially report failed items

        Parameters
        ----------
        event_type: EventType
            Whether this is a SQS, DynamoDB Streams, or Kinesis Data Stream event
        model: Optional["BatchTypeModels"]
            Parser's data model using either SqsRecordModel, DynamoDBStreamRecordModel, KinesisDataStreamRecord

        Exceptions
        ----------
        BatchProcessingError
            Raised when the entire batch has failed processing
        """
        self.event_type = event_type
        self.model = model
        self.batch_response = copy.deepcopy(self.DEFAULT_RESPONSE)
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

    def response(self):
        """Batch items that failed processing, if any"""
        return self.batch_response

    def _prepare(self):
        """
        Remove results from previous execution.
        """
        self.success_messages.clear()
        self.fail_messages.clear()
        self.batch_response = copy.deepcopy(self.DEFAULT_RESPONSE)

    def _process_record(self, record: dict) -> Union[SuccessResponse, FailureResponse]:
        """
        Process a record with instance's handler

        Parameters
        ----------
        record: dict
            A batch record to be processed.
        """
        data = self._to_batch_type(record=record, event_type=self.event_type, model=self.model)
        try:
            result = self.handler(record=data)
            return self.success_handler(record=record, result=result)
        except Exception:
            return self.failure_handler(record=data, exception=sys.exc_info())

    def _clean(self):
        """
        Report messages to be deleted in case of partial failure.
        """

        if not self._has_messages_to_report():
            return

        if self._entire_batch_failed():
            raise BatchProcessingError(
                msg=f"All records failed processing. {len(self.exceptions)} individual errors logged"
                f"separately below.",
                child_exceptions=self.exceptions,
            )

        messages = self._get_messages_to_report()
        self.batch_response = {"batchItemFailures": [messages]}

    def _has_messages_to_report(self) -> bool:
        if self.fail_messages:
            return True

        logger.debug(f"All {len(self.success_messages)} records successfully processed")
        return False

    def _entire_batch_failed(self) -> bool:
        return len(self.exceptions) == len(self.records)

    def _get_messages_to_report(self) -> Dict[str, str]:
        """
        Format messages to use in batch deletion
        """
        return self._COLLECTOR_MAPPING[self.event_type]()

    # Event Source Data Classes follow python idioms for fields
    # while Parser/Pydantic follows the event field names to the latter
    def _collect_sqs_failures(self):
        if self.model:
            return {"itemIdentifier": msg.messageId for msg in self.fail_messages}
        return {"itemIdentifier": msg.message_id for msg in self.fail_messages}

    def _collect_kinesis_failures(self):
        if self.model:
            # Pydantic model uses int but Lambda poller expects str
            return {"itemIdentifier": msg.kinesis.sequenceNumber for msg in self.fail_messages}
        return {"itemIdentifier": msg.kinesis.sequence_number for msg in self.fail_messages}

    def _collect_dynamodb_failures(self):
        if self.model:
            return {"itemIdentifier": msg.dynamodb.SequenceNumber for msg in self.fail_messages}
        return {"itemIdentifier": msg.dynamodb.sequence_number for msg in self.fail_messages}

    @overload
    def _to_batch_type(self, record: dict, event_type: EventType, model: "BatchTypeModels") -> "BatchTypeModels":
        ...  # pragma: no cover

    @overload
    def _to_batch_type(self, record: dict, event_type: EventType) -> EventSourceDataClassTypes:
        ...  # pragma: no cover

    def _to_batch_type(self, record: dict, event_type: EventType, model: Optional["BatchTypeModels"] = None):
        if model is not None:
            return model.parse_obj(record)
        return self._DATA_CLASS_MAPPING[event_type](record)
