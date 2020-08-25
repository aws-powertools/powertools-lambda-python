# -*- coding: utf-8 -*-

"""
Batch SQS utilities
"""

from typing import List, Optional

import boto3
from botocore.config import Config

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

from .base import BasePartialProcessor


class PartialSQSProcessor(BasePartialProcessor):
    def __init__(self, config: Optional[Config] = None):
        config = config or Config()
        self.client = boto3.client("sqs", config=config)
        self.success_messages: List = []
        self.fail_messages: List = []

        super().__init__()

    def get_queue_url(self):
        """
        Format QueueUrl from first records entry
        """
        if not getattr(self, "records", None):
            return

        *_, account_id, queue_name = self.records[0]["eventSourceARN"].split(":")
        return f"{self.client._endpoint.host}/{account_id}/{queue_name}"

    def get_entries_to_clean(self):
        """
        Format messages to use in batch deletion
        """
        return [{"Id": msg["messageId"], "ReceiptHandle": msg["receiptHandle"]} for msg in self.success_messages]

    def _process_record(self, record):
        try:
            result = self.handler(record)
            return self.success_handler(record, result)
        except Exception as exc:
            return self.failure_handler(record, exc)

    def _prepare(self):
        """
        Remove results from previous executions.
        """
        self.success_messages.clear()
        self.fail_messages.clear()

    def _clean(self):
        """
        Delete messages from Queue in case of partial failure.
        """
        if not (self.fail_messages and self.success_messages):
            return

        queue_url = self.get_queue_url()
        entries_to_remove = self.get_entries_to_clean()

        return self.client.delete_message_batch(QueueUrl=queue_url, Entries=entries_to_remove)


@lambda_handler_decorator
def partial_sqs_processor(handler, event, context, record_handler, processor=None):
    records = event["Records"]
    processor = processor or PartialSQSProcessor()

    with processor(records, record_handler) as ctx:
        ctx.process()

    return handler(event, context)
