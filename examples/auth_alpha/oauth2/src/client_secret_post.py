import os

from aws_lambda_powertools.utilities.auth_alpha import OAuth2Client
from aws_lambda_powertools.utilities.typing import LambdaContext

# Create outside the handler so warm invocations can reuse the token cache.
# A callable client_secret loader is also supported, as in client_credentials.py.
inventory_api = OAuth2Client(
    token_url=os.environ["TOKEN_URL"],
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    auth_method="client_secret_post",
    scopes=["inventory:read"],
)
INVENTORY_URL = os.environ["INVENTORY_URL"]


def lambda_handler(event: dict, context: LambdaContext):
    response = inventory_api.request("GET", INVENTORY_URL, timeout=5)
    if response.status != 200:
        raise RuntimeError("Inventory lookup failed")
    return response.json()
