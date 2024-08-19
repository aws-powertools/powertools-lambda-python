from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from typing_extensions import deprecated

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.batch import (
    AsyncBatchProcessor,
    BasePartialBatchProcessor,
    BatchProcessor,
    EventType,
)
from aws_lambda_powertools.warnings import PowertoolsDeprecationWarning

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.batch.types import PartialItemFailureResponse
    from aws_lambda_powertools.utilities.typing import LambdaContext


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

    Examples
    --------
    **Processes Lambda's event with a BasePartialProcessor**
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

    Examples
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
    event: dict,
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

    Examples
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
        records: list[dict] = event.get("Records", [])
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
    event: dict,
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

    Examples
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
        records: list[dict] = event.get("Records", [])
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
