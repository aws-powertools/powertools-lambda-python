# -*- coding: utf-8 -*-

"""
Batch processing utility
"""

from .base import BasePartialProcessor, batch_processor
from .sns import SNSProcessor
from .sqs import PartialSQSProcessor, sqs_batch_processor

__all__ = ("BasePartialProcessor", "PartialSQSProcessor", "batch_processor", "sqs_batch_processor", "SNSProcessor")
