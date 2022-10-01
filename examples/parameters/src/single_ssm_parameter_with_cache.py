from typing import Any

import requests

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext):
    try:
        # Retrieve a single parameter with 20s cache
        endpoint_comments: Any = parameters.get_parameter("/lambda-powertools/endpoint_comments", max_age=20)

        # the value of this parameter is https://jsonplaceholder.typicode.com/comments/
        comments: requests.Response = requests.get(endpoint_comments)

        return {"comments": comments.json()[:10], "statusCode": 200}
    except parameters.exceptions.GetParameterError as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
