from typing import Any

import requests
from custom_provider_s3 import S3Provider

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

s3_provider = S3Provider(bucket_name="bucket_name")


def lambda_handler(event: dict, context: LambdaContext):

    try:
        # Retrieve a single parameter using key
        endpoint_comments: Any = s3_provider.get("comments_endpoint")
        # you can get all parameters using get_multiple and specifying a bucket prefix
        # # for testing purposes we will not use it
        all_parameters: Any = s3_provider.get_multiple("/")
        logger.info(all_parameters)

        # the value of this parameter is https://jsonplaceholder.typicode.com/comments/
        comments: requests.Response = requests.get(endpoint_comments)

        return {"comments": comments.json()[:10], "statusCode": 200}
    # general exception
    except Exception as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
