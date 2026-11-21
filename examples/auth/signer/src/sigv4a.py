import os

import requests

from aws_lambda_powertools.utilities.auth import SigV4aSigner
from aws_lambda_powertools.utilities.typing import LambdaContext

MRAP_ALIAS = os.environ["MRAP_ALIAS"]  # S3 Multi-Region Access Point alias

# One ECDSA signature valid in both regions; needs pip install "aws-lambda-powertools[auth-sigv4a]"
s3_global = SigV4aSigner(service="s3", region_set=["us-east-1", "eu-west-1"])


def lambda_handler(event: dict, context: LambdaContext) -> str:
    url = f"https://{MRAP_ALIAS}.accesspoint.s3-global.amazonaws.com/{event['key']}"
    response = requests.get(url, auth=s3_global.requests_auth(), timeout=5)
    response.raise_for_status()
    return response.text
