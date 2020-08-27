# -*- coding: utf-8 -*-

"""
Middlewares for batch utilities
"""
from typing import Callable, Dict

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

from .base import BaseProcessor


@lambda_handler_decorator
def batch_processor(
    handler: Callable, event: Dict, context: Dict, record_handler: Callable, processor: BaseProcessor = None
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
        >>> @batch_processor(record_handler=record_handler, processor=PartialSQSProcessor)
        >>> def handler(event, context):
        >>>     return {"StatusCode": 200}

    Limitations
    -----------
    * Async batch processors

    """
    records = event["Records"]

    with processor(records, record_handler) as ctx:
        ctx.process()

    return handler(event, context)
