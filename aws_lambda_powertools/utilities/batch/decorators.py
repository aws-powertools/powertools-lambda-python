from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from typing_extensions import deprecated

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.batch import (
    AsyncBatchProcessor,
    BasePartialBatchProcessor,
    BatchProcessor,
    EventType,
)
from aws_lambda_powertools.utilities.batch.exceptions import UnexpectedBatchTypeError
from aws_lambda_powertools.warnings import PowertoolsDeprecationWarning

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aws_lambda_powertools.utilities.batch.types import PartialItemFailureResponse
    from aws_lambda_powertools.utilities.typing import LambdaContext


def _get_records_from_event(
    event: dict[str, Any],
    processor: BasePartialBatchProcessor,
) -> list[dict]:
    """
    Extract records from the event based on the processor's event type.

    For SQS, Kinesis, and DynamoDB: Records are in event["Records"] as a list
    For Kafka: Records are in event["records"] as a dict with topic-partition keys

    Parameters
    ----------
    event: dict
        Lambda's original event
    processor: BasePartialBatchProcessor
        Batch Processor to determine event type

    Returns
    -------
    records: list[dict]
        Flattened list of records to process
    """
    # Kafka events use lowercase "records" and have a nested dict structure
    if processor.event_type == EventType.Kafka:
        kafka_records = event.get("records", {})
        if not kafka_records or not isinstance(kafka_records, dict):
            raise UnexpectedBatchTypeError(
                "Invalid Kafka event structure. Expected 'records' to be a non-empty dict with topic-partition keys.",
            )
        # Flatten the nested dict: {"topic-0": [r1, r2], "topic-1": [r3]} -> [r1, r2, r3]
        return [record for topic_records in kafka_records.values() for record in topic_records]

    # SQS, Kinesis, DynamoDB use uppercase "Records" as a list
    records = event.get("Records", [])
    if not records or not isinstance(records, list):
        raise UnexpectedBatchTypeError(
            "Unexpected batch event type. Possible values are: SQS, KinesisDataStreams, DynamoDBStreams, Kafka",
        )
    return records


@lambda_handler_decorator
@deprecated(
    "`async_batch_processor` decorator is deprecated; use `async_process_partial_response` function instead.",
    category=None,
)
def async_batch_processor(
    handler: Callable,
    event: dict,
    context: LambdaContext,
    record_handler: Callable[..., Awaitable[Any]],
    processor: AsyncBatchProcessor,
):
    """
    Middleware to handle batch event processing

    Notes
    -----
    Consider using async_process_partial_response function for an easier experience.

    Parameters
    ----------
    handler: Callable
        Lambda's handler
    event: dict
        Lambda's Event
    context: LambdaContext
        Lambda's Context
    record_handler: Callable[..., Awaitable[Any]]
        Callable to process each record from the batch
    processor: AsyncBatchProcessor
        Batch Processor to handle partial failure cases

    Example
    --------
        >>> from aws_lambda_powertools.utilities.batch import async_batch_processor, AsyncBatchProcessor
        >>> from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
        >>>
        >>> processor = AsyncBatchProcessor(event_type=EventType.SQS)
        >>>
        >>> async def async_record_handler(record: SQSRecord):
        >>>     payload: str = record.body
        >>>     return payload
        >>>
        >>> @async_batch_processor(record_handler=async_record_handler, processor=processor)
        >>> def lambda_handler(event, context):
        >>>     return processor.response()

    Limitations
    -----------
    * Sync batch processors. Use `batch_processor` instead.
    """

    warnings.warn(
        "The `async_batch_processor` decorator is deprecated in V3 "
        "and will be removed in the next major version. Use `async_process_partial_response` function instead.",
        category=PowertoolsDeprecationWarning,
        stacklevel=2,
    )

    records = event["Records"]

    with processor(records, record_handler, lambda_context=context):
        processor.async_process()

    return handler(event, context)


@lambda_handler_decorator
@deprecated(
    "`batch_processor` decorator is deprecated; use `process_partial_response` function instead.",
    category=None,
)
def batch_processor(
    handler: Callable,
    event: dict,
    context: LambdaContext,
    record_handler: Callable,
    processor: BatchProcessor,
):
    """
    Middleware to handle batch event processing

    Notes
    -----
    Consider using process_partial_response function for an easier experience.

    Parameters
    ----------
    handler: Callable
        Lambda's handler
    event: dict
        Lambda's Event
    context: LambdaContext
        Lambda's Context
    record_handler: Callable
        Callable or corutine to process each record from the batch
    processor: BatchProcessor
        Batch Processor to handle partial failure cases

    Example
    --------
    **Processes Lambda's event with a BatchProcessor**

        >>> from aws_lambda_powertools.utilities.batch import batch_processor, BatchProcessor, EventType
        >>> from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
        >>>
        >>> processor = BatchProcessor(EventType.SQS)
        >>>
        >>> def record_handler(record):
        >>>     return record["body"]
        >>>
        >>> @batch_processor(record_handler=record_handler, processor=BatchProcessor())
        >>> def handler(event, context):
        >>>     return processor.response()

    Limitations
    -----------
    * Async batch processors. Use `async_batch_processor` instead.
    """

    warnings.warn(
        "The `batch_processor` decorator is deprecated in V3 "
        "and will be removed in the next major version. Use `process_partial_response` function instead.",
        category=PowertoolsDeprecationWarning,
        stacklevel=2,
    )

    records = event["Records"]

    with processor(records, record_handler, lambda_context=context):
        processor.process()

    return handler(event, context)


def process_partial_response(
    event: dict[str, Any],
    record_handler: Callable,
    processor: BasePartialBatchProcessor,
    context: LambdaContext | None = None,
) -> PartialItemFailureResponse:
    """
    Higher level function to handle batch event processing.

    Parameters
    ----------
    event: dict
        Lambda's original event
    record_handler: Callable
        Callable to process each record from the batch
    processor: BasePartialBatchProcessor
        Batch Processor to handle partial failure cases
    context: LambdaContext
        Lambda's context, used to optionally inject in record handler

    Returns
    -------
    result: PartialItemFailureResponse
        Lambda Partial Batch Response

    Example
    --------
    **Processes Lambda's SQS event**

    ```python
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, process_partial_response
    from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord

    processor = BatchProcessor(EventType.SQS)

    def record_handler(record: SQSRecord):
        return record.body

    def handler(event, context):
        return process_partial_response(
            event=event, record_handler=record_handler, processor=processor, context=context
        )
    ```

    Limitations
    -----------
    * Async batch processors. Use `async_process_partial_response` instead.
    """
    try:
        records = _get_records_from_event(event, processor)
    except AttributeError:
        event_types = ", ".join(list(EventType.__members__))
        docs = "https://docs.powertools.aws.dev/lambda/python/latest/utilities/batch/#processing-messages-from-sqs"  # noqa: E501 # long-line
        raise ValueError(
            f"Invalid event format. Please ensure batch event is a valid {processor.event_type.value} event. \n"
            f"See sample events in our documentation for either {event_types}: \n {docs}",
        )

    with processor(records, record_handler, context):
        processor.process()

    return processor.response()


def async_process_partial_response(
    event: dict[str, Any],
    record_handler: Callable,
    processor: AsyncBatchProcessor,
    context: LambdaContext | None = None,
) -> PartialItemFailureResponse:
    """
    Higher level function to handle batch event processing asynchronously.

    Parameters
    ----------
    event: dict
        Lambda's original event
    record_handler: Callable
        Callable to process each record from the batch
    processor: AsyncBatchProcessor
        Batch Processor to handle partial failure cases
    context: LambdaContext
        Lambda's context, used to optionally inject in record handler

    Returns
    -------
    result: PartialItemFailureResponse
        Lambda Partial Batch Response

    Example
    --------
    **Processes Lambda's SQS event**

    ```python
    from aws_lambda_powertools.utilities.batch import AsyncBatchProcessor, EventType, process_partial_response
    from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord

    processor = BatchProcessor(EventType.SQS)

    async def record_handler(record: SQSRecord):
        return record.body

    def handler(event, context):
        return async_process_partial_response(
            event=event, record_handler=record_handler, processor=processor, context=context
        )
    ```

    Limitations
    -----------
    * Sync batch processors. Use `process_partial_response` instead.
    """
    try:
        records = _get_records_from_event(event, processor)
    except AttributeError:
        event_types = ", ".join(list(EventType.__members__))
        docs = "https://docs.powertools.aws.dev/lambda/python/latest/utilities/batch/#processing-messages-from-sqs"  # noqa: E501 # long-line
        raise ValueError(
            f"Invalid event format. Please ensure batch event is a valid {processor.event_type.value} event. \n"
            f"See sample events in our documentation for either {event_types}: \n {docs}",
        )

    with processor(records, record_handler, context):
        processor.async_process()

    return processor.response()
