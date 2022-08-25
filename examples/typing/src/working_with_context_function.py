from time import sleep

import requests

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def lambda_handler(event, context: LambdaContext) -> dict:

    limit_execution: int = 1000  # milliseconds

    # scrape website and exit before lambda timeout
    while context.get_remaining_time_in_millis() > limit_execution:

        comments: requests.Response = requests.get("https://jsonplaceholder.typicode.com/comments")
        # add logic here and save the results of the request to an S3 bucket, for example.

        logger.info(
            {
                "operation": "scrape_website",
                "request_id": context.aws_request_id,
                "remaining_time": context.get_remaining_time_in_millis(),
                "comments": comments.json()[:2],
            }
        )

        sleep(1)

    return {"message": "Success"}
