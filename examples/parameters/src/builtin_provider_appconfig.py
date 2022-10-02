from typing import Any

import requests
from botocore.config import Config

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext

config = Config(region_name="sa-east-1")
appconf_provider = parameters.AppConfigProvider(environment="dev", application="comments", config=config)


def lambda_handler(event: dict, context: LambdaContext):
    try:
        # Retrieve a single parameter
        endpoint_comments: Any = appconf_provider.get("config")

        # the value of this parameter is https://jsonplaceholder.typicode.com/comments/
        comments: requests.Response = requests.get(endpoint_comments)

        return {"comments": comments.json()[:10], "statusCode": 200}
    except parameters.exceptions.GetParameterError as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
