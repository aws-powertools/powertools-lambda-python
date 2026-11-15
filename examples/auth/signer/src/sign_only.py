import json
import os

import urllib3

from aws_lambda_powertools.utilities.auth import SigV4Signer
from aws_lambda_powertools.utilities.typing import LambdaContext

APPSYNC_URL = os.environ["APPSYNC_URL"]  # AppSync GraphQL endpoint with IAM authorization

appsync = SigV4Signer(service="appsync")
http = urllib3.PoolManager()


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    body = json.dumps({"query": "query { getOrder(id: $id) { status } }", "variables": {"id": event["order_id"]}})

    # sign() never sends anything; use the signed URL, headers and body with any HTTP client
    signed = appsync.sign("POST", APPSYNC_URL, headers={"content-type": "application/json"}, body=body)
    response = http.request(signed.method, signed.url, headers=signed.headers, body=signed.body, timeout=5)
    return json.loads(response.data)
