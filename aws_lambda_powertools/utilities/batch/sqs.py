# -*- coding: utf-8 -*-

"""
Batch SQS utilities
"""
import logging
import math
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

import boto3
from botocore.config import Config

from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord

from ...middleware_factory import lambda_handler_decorator
from .base import BasePartialProcessor
from .exceptions import SQSBatchProcessingError

logger = logging.getLogger(__name__)


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
    boto3_session : boto3.session.Session, optional
            Boto3 session to use for AWS API communication


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

    def __init__(
        self,
        config: Optional[Config] = None,
        suppress_exception: bool = False,
        boto3_session: Optional[boto3.session.Session] = None,
    ):
        """
        Initializes sqs client.
        """
        config = config or Config()
        session = boto3_session or boto3.session.Session()
        self.client = session.client("sqs", config=config)
        self.suppress_exception = suppress_exception
        self.max_message_batch = 10

        warnings.warn(
            "The sqs_batch_processor decorator and PartialSQSProcessor class are now deprecated, "
            "and will be removed in the next major version. "
            "Please follow the upgrade guide at "
            "https://awslabs.github.io/aws-lambda-powertools-python/latest/utilities/batch/#legacy "
            "to use the native batch_processor decorator or BatchProcessor class."
        )

        super().__init__()

    def _get_queue_url(self) -> Optional[str]:
        """
        Format QueueUrl from first records entry
        """
        if not getattr(self, "records", None):
            return None

        *_, account_id, queue_name = self.records[0]["eventSourceARN"].split(":")
        return f"{self.client._endpoint.host}/{account_id}/{queue_name}"

    def _get_entries_to_clean(self) -> List[Dict[str, str]]:
        """
        Format messages to use in batch deletion
        """
        entries = []
        # success_messages has generic type of union of SQS, Dynamodb and Kinesis Streams records or Pydantic models.
        # Here we get SQS Record only
        messages = cast(List[SQSRecord], self.success_messages)
        for msg in messages:
            entries.append({"Id": msg["messageId"], "ReceiptHandle": msg["receiptHandle"]})
        return entries

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

    def _prepare(self):
        """
        Remove results from previous execution.
        """
        self.success_messages.clear()
        self.fail_messages.clear()

    def _clean(self) -> Optional[List]:
        """
        Delete messages from Queue in case of partial failure.
        """

        # If all messages were successful, fall back to the default SQS -
        # Lambda behavior which deletes messages if Lambda responds successfully
        if not self.fail_messages:
            logger.debug(f"All {len(self.success_messages)} records successfully processed")
            return None

        queue_url = self._get_queue_url()
        if queue_url is None:
            logger.debug("No queue url found")
            return None

        entries_to_remove = self._get_entries_to_clean()
        # Batch delete up to 10 messages at a time (SQS limit)
        max_workers = math.ceil(len(entries_to_remove) / self.max_message_batch)

        if entries_to_remove:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures, results = [], []
                while entries_to_remove:
                    futures.append(
                        executor.submit(
                            self._delete_messages, queue_url, entries_to_remove[: self.max_message_batch], self.client
                        )
                    )
                    entries_to_remove = entries_to_remove[self.max_message_batch :]
                for future in as_completed(futures):
                    try:
                        logger.debug("Deleted batch of processed messages from SQS")
                        results.append(future.result())
                    except Exception:
                        logger.exception("Couldn't remove batch of processed messages from SQS")
                        raise
        if self.suppress_exception:
            logger.debug(f"{len(self.fail_messages)} records failed processing, but exceptions are suppressed")
        else:
            logger.debug(f"{len(self.fail_messages)} records failed processing, raising exception")
            raise SQSBatchProcessingError(
                msg=f"Not all records processed successfully. {len(self.exceptions)} individual errors logged "
                f"separately below.",
                child_exceptions=self.exceptions,
            )

        return results

    def _delete_messages(self, queue_url: str, entries_to_remove: List, sqs_client: Any):
        delete_message_response = sqs_client.delete_message_batch(
            QueueUrl=queue_url,
            Entries=entries_to_remove,
        )
        return delete_message_response


@lambda_handler_decorator
def sqs_batch_processor(
    handler: Callable,
    event: Dict,
    context: Dict,
    record_handler: Callable,
    config: Optional[Config] = None,
    suppress_exception: bool = False,
    boto3_session: Optional[boto3.session.Session] = None,
):
    """
    Middleware to handle SQS batch event processing

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
    config: Config
            botocore config object
    suppress_exception: bool, optional
        Supress exception raised if any messages fail processing, by default False
    boto3_session : boto3.session.Session, optional
            Boto3 session to use for AWS API communication

    Examples
    --------
    **Processes Lambda's event with PartialSQSProcessor**

        >>> from aws_lambda_powertools.utilities.batch import sqs_batch_processor
        >>>
        >>> def record_handler(record):
        >>>      return record["body"]
        >>>
        >>> @sqs_batch_processor(record_handler=record_handler)
        >>> def handler(event, context):
        >>>     return {"StatusCode": 200}

    Limitations
    -----------
    * Async batch processors

    """
    config = config or Config()
    session = boto3_session or boto3.session.Session()

    processor = PartialSQSProcessor(config=config, suppress_exception=suppress_exception, boto3_session=session)

    records = event["Records"]

    with processor(records, record_handler):
        processor.process()

    return handler(event, context)
