from typing import Any

import requests

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext):

    try:
        # Usually an endpoint is not sensitive data, so we store it in SSM Parameters
        endpoint_comments: Any = parameters.get_parameter("/lambda-powertools/endpoint_comments")

        # An API-KEY is a sensitive data and should be stored in SecretsManager
        # set-secret will create a new secret if it doesn't exist and return the version id
        update_secret = parameters.set_secret(name="/lambda-powertools/api-key", value="3884c335-25b0-4267-8531-561777eb2078")

        headers: dict = {"X-API-Key": api_key}

        comments: requests.Response = requests.get(endpoint_comments, headers=headers)

        return {"comments": comments.json()[:10], "statusCode": 200}
    except parameters.exceptions.GetParameterError as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
