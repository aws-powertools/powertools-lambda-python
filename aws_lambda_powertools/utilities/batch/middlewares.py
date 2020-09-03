# -*- coding: utf-8 -*-

"""
Middlewares for batch utilities
"""
from typing import Callable, Dict, Optional

from botocore.config import Config

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

from .base import BasePartialProcessor
from .sqs import PartialSQSProcessor


@lambda_handler_decorator
def batch_processor(
    handler: Callable, event: Dict, context: Dict, record_handler: Callable, processor: BasePartialProcessor = None
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
        >>> @batch_processor(record_handler=record_handler, processor=PartialSQSProcessor())
        >>> def handler(event, context):
        >>>     return {"StatusCode": 200}

    Limitations
    -----------
    * Async batch processors

    """
    records = event["Records"]

    with processor(records, record_handler):
        processor.process()

    return handler(event, context)


@lambda_handler_decorator
def sqs_batch_processor(
    handler: Callable,
    event: Dict,
    context: Dict,
    record_handler: Callable,
    config: Optional[Config] = None,
    suppress_exception: bool = False,
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

    Examples
    --------
    **Processes Lambda's event with PartialSQSProcessor**
        >>> from aws_lambda_powertools.utilities.batch import sqs_batch_processor
        >>>
        >>> def record_handler(record):
        >>>     return record["body"]
        >>>
        >>> @sqs_batch_processor(record_handler=record_handler)
        >>> def handler(event, context):
        >>>     return {"StatusCode": 200}

    Limitations
    -----------
    * Async batch processors

    """
    config = config or Config()
    processor = PartialSQSProcessor(config=config, suppress_exception=suppress_exception)

    records = event["Records"]

    with processor(records, record_handler):
        processor.process()

    return handler(event, context)
