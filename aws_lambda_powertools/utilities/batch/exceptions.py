"""
Batch processing exceptions
"""


class SQSBatchProcessingError(Exception):
    """When at least one message within a batch could not be processed"""
