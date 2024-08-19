from __future__ import annotations

from typing import TYPE_CHECKING

import boto3

from aws_lambda_powertools import Logger

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

boto3.set_stream_logger()
boto3.set_stream_logger("botocore")

logger = Logger()
client = boto3.client("s3")


def lambda_handler(event: dict, context: LambdaContext) -> list:
    response = client.list_buckets()

    return response.get("Buckets", [])
