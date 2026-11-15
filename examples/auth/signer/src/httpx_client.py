import os

import httpx

from aws_lambda_powertools.utilities.auth import SigV4Signer
from aws_lambda_powertools.utilities.typing import LambdaContext

FUNCTION_URL = os.environ["PRICING_FUNCTION_URL"]  # Lambda Function URL with AWS_IAM auth

pricing = SigV4Signer(service="lambda")
client = httpx.Client(base_url=FUNCTION_URL, auth=pricing.httpx_auth(), timeout=5)


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    response = client.get("/quote", params={"sku": event["sku"], "qty": event["qty"]})
    response.raise_for_status()
    return response.json()
