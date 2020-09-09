# -*- coding: utf-8 -*-

"""
Batch SNS utilities
"""
import logging
from abc import ABC
from typing import Any, Callable, List, Optional

logger = logging.getLogger(__name__)


class SNSProcessor(ABC):
    """
    Amazon SNS batch processor

    Example
    -------
    **Process batch triggered by SNS**

        >>> from aws_lambda_powertools.utilities.batch import SNSProcessor
        >>>
        >>> def record_handler(message: str) -> None:
        >>>     # Logic to handle the message
        >>>
        >>> def handler(event, context):
        >>>     records = event["Records"]
        >>>     processor = SNSProcessor()
        >>>
        >>>     with processor(records=records, handler=record_handler):
        >>>         result = processor.process()
        >>>
        >>>     return result

    **Process batch events using batch_processor**
        >>> from aws_lambda_powertools.utilities.batch import batch_processor, SNSProcessor
        >>>
        >>> def record_handler(message: str) -> None:
        >>>     # Logic to handle the message
        >>>
        >>> @batch_processor(record_handler=record_handler, processor=SNSProcessor())
        >>> def handler(event, context):
        >>>     return {"StatusCode": 200}
    """

    def process(self) -> List[Any]:
        """
        Call instance's handler for each record.
        """
        return [self._process_record(record) for record in self.records]

    def _process_record(self, record: Any) -> Optional[Any]:
        """
        Process a record with instance's handler

        Parameters
        ----------
        record: Any
            An object to be processed.
        """
        try:
            result = self.handler(record["Sns"]["Message"])
        except Exception as exc:
            logger.warning("Failed to handle the given record.", exc)
            result = None

        return result

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

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass
