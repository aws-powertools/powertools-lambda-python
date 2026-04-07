"""OpenAPI module for AWS Lambda Powertools."""

from aws_lambda_powertools.event_handler.openapi.exceptions import OpenAPIMergeError
from aws_lambda_powertools.event_handler.openapi.merge import OpenAPIMerge

__all__ = [
    "OpenAPIMerge",
    "OpenAPIMergeError",
]
