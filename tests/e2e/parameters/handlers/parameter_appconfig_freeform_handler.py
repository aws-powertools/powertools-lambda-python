from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext):
    # Retrieve a single configuration, latest version
    value: bytes = parameters.get_app_config(
        name=event.get("name"),
        environment=event.get("environment"),
        application=event.get("application"),
    )

    return value
