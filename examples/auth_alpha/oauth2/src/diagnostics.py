import os
from urllib.parse import quote

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.auth_alpha import OAuth2Client
from aws_lambda_powertools.utilities.auth_alpha.oauth2.exceptions import DownstreamRequestError, TokenExchangeError
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
INVENTORY_URL = os.environ["INVENTORY_URL"]
inventory_api = OAuth2Client(
    token_url=os.environ["TOKEN_URL"],
    client_id=os.environ["CLIENT_ID"],
    client_secret=lambda: os.environ["CLIENT_SECRET"],
    scopes=["inventory:read"],
    audience=INVENTORY_URL,
)


def lambda_handler(event: dict, context: LambdaContext):
    sku = quote(event["sku"], safe="")
    try:
        response = inventory_api.request("GET", f"{INVENTORY_URL}/stock/{sku}")
    except (TokenExchangeError, DownstreamRequestError) as error:
        logger.warning("Inventory request unavailable", reason=error.reason.value, retryable=error.retryable)
        return {"statusCode": 502, "body": "Inventory request unavailable"}
    if response.status != 200:
        return {"statusCode": 502, "body": "Inventory request unavailable"}
    return response.json()
