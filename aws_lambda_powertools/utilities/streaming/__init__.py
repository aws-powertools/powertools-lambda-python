"""
The streaming utility handles datasets larger than the available memory as streaming data.
!!! abstract "Usage Documentation"
    [`Streaming`](../utilities/streaming.md)
"""

from aws_lambda_powertools.utilities.streaming.s3_object import S3Object

__all__ = ["S3Object"]
