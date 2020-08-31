# -*- coding: utf-8 -*-

"""
Batch processing utility
"""

from .base import BasePartialProcessor
from .middlewares import batch_processor
from .sqs import PartialSQSProcessor

__all__ = (
    "BasePartialProcessor",
    "PartialSQSProcessor",
    "batch_processor",
)
