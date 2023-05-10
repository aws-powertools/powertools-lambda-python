import os
import sys
from random import randint
from typing import Any

import boto3

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.batch import (
    BasePartialBatchProcessor,
    EventType,
    process_partial_response,
)

table_name = os.getenv("TABLE_NAME", "table_not_found")

logger = Logger()


class MyPartialProcessor(BasePartialBatchProcessor):
    """
    Process a record and stores successful results at a Amazon DynamoDB Table

    Parameters
    ----------
    table_name: str
        DynamoDB table name to write results to
    """

    def __init__(self, table_name: str):
        self.table_name = table_name

        super().__init__(event_type=EventType.SQS)

    def _prepare(self):
        # It's called once, *before* processing
        # Creates table resource and clean previous results
        self.ddb_table = boto3.resource("dynamodb").Table(self.table_name)
        self.success_messages.clear()

    def _clean(self):
        # It's called once, *after* closing processing all records (closing the context manager)
        # Here we're sending, at once, all successful messages to a ddb table
        with self.ddb_table.batch_writer() as batch:
            for result in self.success_messages:
                batch.put_item(Item=result)

    def _process_record(self, record):
        # It handles how your record is processed
        # Here we're keeping the status of each run
        # where self.handler is the record_handler function passed as an argument
        try:
            result = self.handler(record)  # record_handler passed to decorator/context manager
            return self.success_handler(record, result)
        except Exception as exc:
            logger.error(exc)
            return self.failure_handler(record, sys.exc_info())

    def success_handler(self, record, result: Any):
        entry = ("success", result, record)
        self.success_messages.append(record)
        return entry

    async def _async_process_record(self, record: dict):
        raise NotImplementedError()


processor = MyPartialProcessor(table_name)


def record_handler(record):
    return randint(0, 100)


def lambda_handler(event, context):
    return process_partial_response(event=event, record_handler=record_handler, processor=processor, context=context)
