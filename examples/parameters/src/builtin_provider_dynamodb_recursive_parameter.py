from typing import Any

import requests

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext

dynamodb_provider = parameters.DynamoDBProvider(table_name="ParameterTable")


def lambda_handler(event: dict, context: LambdaContext):

    try:
        # Retrieve multiple parameters using HASH KEY
        all_parameters: Any = dynamodb_provider.get_multiple("config")
        endpoint_comments = "https://jsonplaceholder.typicode.com/noexists/"
        limit = 2

        for parameter, value in all_parameters.items():

            if parameter == "endpoint_comments":
                endpoint_comments = value

            if parameter == "limit":
                limit = int(value)

        # the value of parameter is https://jsonplaceholder.typicode.com/comments/
        comments: requests.Response = requests.get(endpoint_comments)

        return {"comments": comments.json()[limit]}
    # general exception
    except Exception as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
