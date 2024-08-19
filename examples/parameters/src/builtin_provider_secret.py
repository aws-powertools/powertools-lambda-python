from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests
from botocore.config import Config

from aws_lambda_powertools.utilities import parameters

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

config = Config(region_name="sa-east-1", connect_timeout=1, retries={"total_max_attempts": 2, "max_attempts": 5})
ssm_provider = parameters.SecretsProvider(config=config)


def lambda_handler(event: dict, context: LambdaContext):

    try:
        # Usually an endpoint is not sensitive data, so we store it in SSM Parameters
        endpoint_comments: Any = parameters.get_parameter("/lambda-powertools/endpoint_comments")
        # An API-KEY is a sensitive data and should be stored in SecretsManager
        api_key: Any = ssm_provider.get("/lambda-powertools/api-key")

        headers: dict = {"X-API-Key": api_key}

        comments: requests.Response = requests.get(endpoint_comments, headers=headers)

        return {"comments": comments.json()[:10], "statusCode": 200}
    except parameters.exceptions.GetParameterError as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
