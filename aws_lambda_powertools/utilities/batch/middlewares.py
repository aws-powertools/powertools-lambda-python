# -*- coding: utf-8 -*-

"""
Middlewares for batch utilities
"""
from typing import Callable, Dict

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

from .sqs import PartialSQSProcessor


@lambda_handler_decorator
def partial_sqs_processor(
    handler: Callable, event: Dict, context: Dict, record_handler: Callable, processor: PartialSQSProcessor = None
):
    """

    Examples
    --------

    """
    records = event["Records"]
    processor = processor or PartialSQSProcessor()

    with processor(records, record_handler) as ctx:
        ctx.process()

    return handler(event, context)
