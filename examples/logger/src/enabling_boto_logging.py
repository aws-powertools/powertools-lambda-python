from typing import Dict, List

import boto3

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

boto3.set_stream_logger()
boto3.set_stream_logger("botocore")

logger = Logger()
client = boto3.client("s3")


def handler(event: Dict, context: LambdaContext) -> List:
    response = client.list_buckets()

    return response.get("Buckets", [])
