from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests

from aws_lambda_powertools.utilities import parameters

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

dynamodb_provider = parameters.DynamoDBProvider(table_name="ParameterTable")


def lambda_handler(event: dict, context: LambdaContext):

    try:
        # Usually an endpoint is not sensitive data, so we store it in DynamoDB Table
        endpoint_comments: Any = dynamodb_provider.get("comments_endpoint")

        comments: requests.Response = requests.get(endpoint_comments)

        return {"comments": comments.json()[:10], "statusCode": 200}
    # general exception
    except Exception as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
