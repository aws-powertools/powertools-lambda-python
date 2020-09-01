# -*- coding: utf-8 -*-

"""
Batch SQS utilities
"""
from typing import List, Optional, Tuple

import boto3
from botocore.config import Config

from .base import BasePartialProcessor


class PartialSQSProcessor(BasePartialProcessor):
    """
    Amazon SQS batch processor to delete successes from the Queue.

    Only the **special** case of partial failure is handled, thus a batch in
    which all records failed is **not** going to be removed from the queue, and
    the same is valid for a full success.

    Parameters
    ----------
    config: Config
        botocore config object

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

    def __init__(self, config: Optional[Config] = None):
        """
        Initializes sqs client.
        """
        config = config or Config()
        self.client = boto3.client("sqs", config=config)

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
        if not (self.fail_messages and self.success_messages):
            return

        queue_url = self._get_queue_url()
        entries_to_remove = self._get_entries_to_clean()

        return self.client.delete_message_batch(QueueUrl=queue_url, Entries=entries_to_remove)
