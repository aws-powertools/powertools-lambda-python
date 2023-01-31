from typing import Any

import hvac
import requests
from custom_provider_vault import VaultProvider

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

# In production you must use Vault over HTTPS and certificates.
vault_provider = VaultProvider(vault_url="http://192.168.68.105:8200/", vault_token="YOUR_TOKEN")


def lambda_handler(event: dict, context: LambdaContext):

    try:
        # Retrieve a single parameter
        endpoint_comments: Any = vault_provider.get("comments_endpoint", transform="json")

        # you can get all parameters using get_multiple and specifying vault mount point
        # # for testing purposes we will not use it
        all_parameters: Any = vault_provider.get_multiple("/")
        logger.info(all_parameters)

        # the value of this parameter is https://jsonplaceholder.typicode.com/comments/
        comments: requests.Response = requests.get(endpoint_comments["url"])

        return {"comments": comments.json()[:10], "statusCode": 200}
    except hvac.exceptions.InvalidPath as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
    # general exception
    except Exception as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
