# -*- coding: utf-8 -*-

"""
Batch processing utility
"""

from .base import BasePartialProcessor, BaseProcessor
from .sqs import PartialSQSProcessor, partial_sqs_processor

__all__ = (
    "BaseProcessor",
    "BasePartialProcessor",
    "PartialSQSProcessor",
    "partial_sqs_processor",
)
