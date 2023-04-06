from typing import Any, Awaitable, Callable, Dict

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.batch import AsyncBatchProcessor, BatchProcessor
from aws_lambda_powertools.utilities.typing import LambdaContext


@lambda_handler_decorator
def async_batch_processor(
    handler: Callable,
    event: Dict,
    context: LambdaContext,
    record_handler: Callable[..., Awaitable[Any]],
    processor: AsyncBatchProcessor,
):
    """
    Middleware to handle batch event processing
    Parameters
    ----------
    handler: Callable
        Lambda's handler
    event: Dict
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
        >>>
        >>> async def async_record_handler(record):
        >>>     payload: str = record.body
        >>>     return payload
        >>>
        >>> processor = AsyncBatchProcessor(event_type=EventType.SQS)
        >>>
        >>> @async_batch_processor(record_handler=async_record_handler, processor=processor)
        >>> async def lambda_handler(event, context: LambdaContext):
        >>>     return processor.response()

    Limitations
    -----------
    * Sync batch processors. Use `batch_processor` instead.
    """
    records = event["Records"]

    with processor(records, record_handler, lambda_context=context):
        processor.async_process()

    return handler(event, context)


@lambda_handler_decorator
def batch_processor(
    handler: Callable, event: Dict, context: LambdaContext, record_handler: Callable, processor: BatchProcessor
):
    """
    Middleware to handle batch event processing

    Parameters
    ----------
    handler: Callable
        Lambda's handler
    event: Dict
        Lambda's Event
    context: LambdaContext
        Lambda's Context
    record_handler: Callable
        Callable or corutine to process each record from the batch
    processor: BatchProcessor
        Batch Processor to handle partial failure cases

    Examples
    --------
    **Processes Lambda's event with a BasePartialProcessor**

        >>> from aws_lambda_powertools.utilities.batch import batch_processor, BatchProcessor
        >>>
        >>> def record_handler(record):
        >>>     return record["body"]
        >>>
        >>> @batch_processor(record_handler=record_handler, processor=BatchProcessor())
        >>> def handler(event, context):
        >>>     return {"StatusCode": 200}

    Limitations
    -----------
    * Async batch processors. Use `async_batch_processor` instead.
    """
    records = event["Records"]

    with processor(records, record_handler, lambda_context=context):
        processor.process()

    return handler(event, context)
