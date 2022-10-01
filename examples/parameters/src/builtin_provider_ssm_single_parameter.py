from typing import Any

import requests
from botocore.config import Config

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext

# changing region_name, connect_timeout and retrie configurations
# see: https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html
config = Config(region_name="sa-east-1", connect_timeout=1, retries={"total_max_attempts": 2, "max_attempts": 5})
ssm_provider = parameters.SSMProvider(config=config)


def lambda_handler(event: dict, context: LambdaContext):
    try:
        # Retrieve a single parameter
        endpoint_comments: Any = ssm_provider.get("/lambda-powertools/endpoint_comments")

        # the value of this parameter is https://jsonplaceholder.typicode.com/comments/
        comments: requests.Response = requests.get(endpoint_comments)

        return {"comments": comments.json()[:10], "statusCode": 200}
    except parameters.exceptions.GetParameterError as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
