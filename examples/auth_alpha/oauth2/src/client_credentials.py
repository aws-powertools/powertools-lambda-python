import os
from urllib.parse import quote

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.auth_alpha import OAuth2Client
from aws_lambda_powertools.utilities.typing import LambdaContext


def load_secret() -> str:
    secret = parameters.get_secret(os.environ["CLIENT_SECRET_NAME"], max_age=300)
    if not isinstance(secret, str):
        raise ValueError("Expected a string client secret")
    return secret


INVENTORY_URL = os.environ["INVENTORY_URL"]

inventory_api = OAuth2Client(
    token_url=os.environ["TOKEN_URL"],
    client_id=os.environ["CLIENT_ID"],
    client_secret=load_secret,
    scopes=["inventory:read"],
    audience=INVENTORY_URL,
)


def lambda_handler(event: dict, context: LambdaContext):
    sku = quote(event["sku"], safe="")
    response = inventory_api.request("GET", f"{INVENTORY_URL}/stock/{sku}", timeout=5)
    if response.status != 200:
        raise RuntimeError("Inventory lookup failed")
    return response.json()
