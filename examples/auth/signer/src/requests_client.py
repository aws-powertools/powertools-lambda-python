import os

import requests

from aws_lambda_powertools.utilities.auth import SigV4Signer
from aws_lambda_powertools.utilities.typing import LambdaContext

ORDERS_API = os.environ["ORDERS_API_URL"]  # API Gateway REST API with IAM authorization

# Region and credentials come from the Lambda execution environment
orders_api = SigV4Signer(service="execute-api")
http = requests.Session()
http.auth = orders_api.requests_auth()  # every request through this session is signed


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    response = http.post(f"{ORDERS_API}/orders", json={"customer_id": event["customer_id"]}, timeout=5)
    response.raise_for_status()
    return response.json()
