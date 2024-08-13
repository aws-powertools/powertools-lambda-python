from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests

from aws_lambda_powertools.utilities import parameters

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext):
    try:
        # Retrieve a single parameter with 20s cache
        endpoint_comments: Any = parameters.get_parameter("/lambda-powertools/endpoint_comments", force_fetch=True)

        # the value of this parameter is https://jsonplaceholder.typicode.com/comments/
        comments: requests.Response = requests.get(endpoint_comments)

        return {"comments": comments.json()[:10], "statusCode": 200}
    except parameters.exceptions.GetParameterError as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
