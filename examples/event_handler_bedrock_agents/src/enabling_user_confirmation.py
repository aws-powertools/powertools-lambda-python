from time import time

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
app = BedrockAgentResolver()


@app.get(
    "/current_time",
    description="Gets the current time in seconds",
    openapi_extensions={"x-requireConfirmation": "ENABLED"},  # (1)!
)
def current_time() -> int:
    return int(time())


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)


if __name__ == "__main__":
    print(app.get_openapi_json_schema())
