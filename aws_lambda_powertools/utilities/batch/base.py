# -*- coding: utf-8 -*-

"""
Batch processing utilities
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Iterable, List, Tuple

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

logger = logging.getLogger(__name__)


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

    def __call__(self, records: Iterable[Any], handler: Callable):
        """
        Set instance attributes before execution

        Parameters
        ----------
        records: Iterable[Any]
            Iterable with objects to be processed.
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

    def failure_handler(self, record: Any, exception: Exception):
        """
        Failure callback

        Returns
        -------
        tuple
            "fail", exceptions args, original record
        """
        entry = ("fail", exception.args, record)
        logger.debug("Record processing exception: ", exception)
        self.exceptions.append(exception)
        self.fail_messages.append(record)
        return entry


@lambda_handler_decorator
def batch_processor(
    handler: Callable, event: Dict, context: Dict, record_handler: Callable, processor: BasePartialProcessor = None
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
        >>> from aws_lambda_powertools.utilities.batch import batch_processor
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
