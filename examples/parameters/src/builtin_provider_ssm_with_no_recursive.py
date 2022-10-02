from typing import Any

import requests

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext

ssm_provider = parameters.SSMProvider()


class ConfigNotFound(Exception):
    ...


def lambda_handler(event: dict, context: LambdaContext):
    try:
        # Retrieve multiple parameters from a path prefix
        # /config = root
        # /config/endpoint = url
        # /config/endpoint/query = querystring
        all_parameters: Any = ssm_provider.get_multiple("/config", recursive=False)
        endpoint_comments = "https://jsonplaceholder.typicode.com/comments/"

        for parameter, value in all_parameters.items():

            # query parameter is used to query endpoint
            if "query" in parameter:
                endpoint_comments = f"{endpoint_comments}{value}"
                break
        else:
            # scheme config was not found because get_multiple is not recursive
            raise ConfigNotFound("URL query parameter was not found")

        # the value of parameter is https://jsonplaceholder.typicode.com/comments/
        comments: requests.Response = requests.get(endpoint_comments)

        return {"comments": comments.json()}
    except parameters.exceptions.GetParameterError as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
