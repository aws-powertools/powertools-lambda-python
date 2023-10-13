"""
    Note: This utility is currently in a Non-General Availability (Non-GA) phase and may have limitations.
    Please DON'T USE THIS utility in production environments.
    Keep in mind that when we transition to General Availability (GA), there might be breaking changes introduced.
"""

from aws_lambda_powertools.utilities._data_masking.base import DataMasking

__all__ = [
    "DataMasking",
]
