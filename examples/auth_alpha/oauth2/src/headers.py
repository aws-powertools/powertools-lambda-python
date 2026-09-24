import os
from urllib.parse import quote, urlsplit

import urllib3

from aws_lambda_powertools.utilities.auth_alpha import OAuth2Client
from aws_lambda_powertools.utilities.typing import LambdaContext

INVENTORY_URL = os.environ["INVENTORY_URL"]
inventory_url = urlsplit(INVENTORY_URL)
if (
    inventory_url.scheme != "https"
    or not inventory_url.hostname
    or inventory_url.username is not None
    or inventory_url.password is not None
    or "#" in INVENTORY_URL
):
    raise ValueError("INVENTORY_URL must be an HTTPS URL without user information or a fragment")

inventory_api = OAuth2Client(
    token_url=os.environ["TOKEN_URL"],
    client_id=os.environ["CLIENT_ID"],
    client_secret=lambda: os.environ["CLIENT_SECRET"],
    scopes=["inventory:read"],
    resource=INVENTORY_URL,
)
http = urllib3.PoolManager()


def lambda_handler(event: dict, context: LambdaContext):
    sku = quote(event["sku"], safe="")
    response = http.request(
        "GET",
        f"{INVENTORY_URL}/stock/{sku}",
        headers=inventory_api.auth_headers(),
        timeout=urllib3.Timeout(total=5),
        redirect=False,
        retries=False,
    )
    if response.status != 200:
        raise RuntimeError("Inventory lookup failed")
    return response.json()
