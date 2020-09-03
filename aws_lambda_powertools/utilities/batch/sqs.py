# -*- coding: utf-8 -*-

"""
Batch SQS utilities
"""
from typing import List, Optional, Tuple

import boto3
from botocore.config import Config

from .base import BasePartialProcessor
from .exceptions import SQSBatchProcessingError


class PartialSQSProcessor(BasePartialProcessor):
    """
    Amazon SQS batch processor to delete successes from the Queue.

    The whole batch will be processed, even if failures occur. After all records are processed,
    SQSBatchProcessingError will be raised if there were any failures, causing messages to
    be returned to the SQS queue. This behaviour can be disabled by passing suppress_exception.

    Parameters
    ----------
    config: Config
        botocore config object
    suppress_exception: bool, optional
        Supress exception raised if any messages fail processing, by default False


    Example
    -------
    **Process batch triggered by SQS**

        >>> from aws_lambda_powertools.utilities.batch import PartialSQSProcessor
        >>>
        >>> def record_handler(record):
        >>>     return record["body"]
        >>>
        >>> def handler(event, context):
        >>>     records = event["Records"]
        >>>     processor = PartialSQSProcessor()
        >>>
        >>>     with processor(records=records, handler=record_handler):
        >>>         result = processor.process()
        >>>
        >>>     # Case a partial failure occurred, all successful executions
        >>>     # have been deleted from the queue after context's exit.
        >>>
        >>>     return result
    """

    def __init__(self, config: Optional[Config] = None, suppress_exception: bool = False):
        """
        Initializes sqs client.
        """
        config = config or Config()
        self.client = boto3.client("sqs", config=config)
        self.suppress_exception = suppress_exception

        super().__init__()

    def _get_queue_url(self) -> Optional[str]:
        """
        Format QueueUrl from first records entry
        """
        if not getattr(self, "records", None):
            return

        *_, account_id, queue_name = self.records[0]["eventSourceARN"].split(":")
        return f"{self.client._endpoint.host}/{account_id}/{queue_name}"

    def _get_entries_to_clean(self) -> List:
        """
        Format messages to use in batch deletion
        """
        return [{"Id": msg["messageId"], "ReceiptHandle": msg["receiptHandle"]} for msg in self.success_messages]

    def _process_record(self, record) -> Tuple:
        """
        Process a record with instance's handler

        Parameters
        ----------
        record: Any
            An object to be processed.
        """
        try:
            result = self.handler(record)
            return self.success_handler(record, result)
        except Exception as exc:
            return self.failure_handler(record, exc)

    def _prepare(self):
        """
        Remove results from previous execution.
        """
        self.success_messages.clear()
        self.fail_messages.clear()

    def _clean(self):
        """
        Delete messages from Queue in case of partial failure.
        """
        # If all messages were successful, fall back to the default SQS -
        # Lambda behaviour which deletes messages if Lambda responds successfully
        if not self.fail_messages:
            return

        queue_url = self._get_queue_url()
        entries_to_remove = self._get_entries_to_clean()

        delete_message_response = self.client.delete_message_batch(QueueUrl=queue_url, Entries=entries_to_remove)

        if self.fail_messages and not self.suppress_exception:
            raise SQSBatchProcessingError(list(self.exceptions))

        return delete_message_response
