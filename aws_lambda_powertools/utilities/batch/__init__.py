# -*- coding: utf-8 -*-

"""
Batch processing utility
"""
from .base import BasePartialProcessor, BaseProcessor
from .middlewares import partial_sqs_processor
from .sqs import PartialSQSProcessor

__all__ = (
    "BaseProcessor",
    "BasePartialProcessor",
    "PartialSQSProcessor",
    "partial_sqs_processor",
)
