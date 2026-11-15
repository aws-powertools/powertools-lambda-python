import os

import requests

from aws_lambda_powertools.utilities.auth import SigV4Signer
from aws_lambda_powertools.utilities.typing import LambdaContext

BUCKET = os.environ["REPORTS_BUCKET"]

# service="s3" applies the S3 canonical URI rules, so keys with spaces or "+" sign correctly
s3 = SigV4Signer(service="s3")


def lambda_handler(event: dict, context: LambdaContext) -> str:
    url = f"https://{BUCKET}.s3.{s3.region}.amazonaws.com/{requests.utils.quote(event['key'])}"
    response = requests.get(url, auth=s3.requests_auth(), timeout=5)
    response.raise_for_status()
    return response.text
