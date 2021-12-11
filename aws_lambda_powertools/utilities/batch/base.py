# -*- coding: utf-8 -*-

"""
Batch processing utilities
"""
import logging
import sys
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

logger = logging.getLogger(__name__)


class EventType(Enum):
    SQS = "SQS"
    KinesisDataStream = "KinesisDataStream"
    DynamoDB = "DynamoDB"


class BasePartialProcessor(ABC):
    """
    Abstract class for batch processors.
    """

    def __init__(self):
        self.success_messages: List = []
        self.fail_messages: List = []
        self.exceptions: List = []

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
    def _process_record(self, record: Any):
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

    def __call__(self, records: List[Any], handler: Callable):
        """
        Set instance attributes before execution

        Parameters
        ----------
        records: List[Any]
            List with objects to be processed.
        handler: Callable
            Callable to process "records" entries.
        """
        self.records = records
        self.handler = handler
        return self

    def success_handler(self, record: Any, result: Any):
        """
        Success callback

        Returns
        -------
        tuple
            "success", result, original record
        """
        entry = ("success", result, record)
        self.success_messages.append(record)
        return entry

    def failure_handler(self, record: Any, exception: Tuple):
        """
        Failure callback

        Returns
        -------
        tuple
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
    DEFAULT_RESPONSE: Dict[str, List[Optional[dict]]] = {"batchItemFailures": []}

    def __init__(self, event_type: EventType):
        """Process batch and partially report failed items

        Parameters
        ----------
        event_type: EventType
            Whether this is a SQS, DynamoDB Streams, or Kinesis Data Stream event
        """
        # refactor: Bring boto3 etc. for deleting permanent exceptions
        self.event_type = event_type
        self.batch_response = self.DEFAULT_RESPONSE

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
        self.batch_response = self.DEFAULT_RESPONSE

    def _process_record(self, record) -> Tuple:
        """
        Process a record with instance's handler

        Parameters
        ----------
        record: Any
            An object to be processed.
        """
        try:
            result = self.handler(record=record)
            return self.success_handler(record=record, result=result)
        except Exception:
            return self.failure_handler(record=record, exception=sys.exc_info())

    def _clean(self):
        """
        Report messages to be deleted in case of partial failure.
        """

        if not self._has_messages_to_report():
            return

        messages = self._get_messages_to_report()
        self.batch_response = {"batchItemFailures": [messages]}

    def _has_messages_to_report(self) -> bool:
        if self.fail_messages:
            return True

        logger.debug(f"All {len(self.success_messages)} records successfully processed")
        return False

    def _get_messages_to_report(self) -> Dict[str, str]:
        """
        Format messages to use in batch deletion
        """
        # Refactor: get message per event type
        return {msg["receiptHandle"]: msg["messageId"] for msg in self.fail_messages}
