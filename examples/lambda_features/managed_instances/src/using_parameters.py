from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    # Cache is per-process, not shared across concurrent requests
    # Each process maintains its own cache
    # This is generally fine - cache will warm up per process
    api_key = parameters.get_secret("my-api-key", max_age=300)  # noqa: F841

    return {"statusCode": 200}
