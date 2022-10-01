from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext):
    # Retrieve a single parameter
    value = parameters.get_parameter("sample_string")

    return {"value": value}
