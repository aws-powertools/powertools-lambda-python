"""
Utility to fetch data from the AWS Lambda Metadata Endpoint
"""

from aws_lambda_powertools.utilities.metadata.exceptions import LambdaMetadataError
from aws_lambda_powertools.utilities.metadata.lambda_metadata import (
    LambdaMetadata,
    clear_metadata_cache,
    get_lambda_metadata,
)

__all__ = [
    "LambdaMetadata",
    "LambdaMetadataError",
    "get_lambda_metadata",
    "clear_metadata_cache",
]
