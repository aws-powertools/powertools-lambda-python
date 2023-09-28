from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    try:
        # Set a single parameter, returns the version ID of the parameter
        parameter_version = parameters.set_parameter(path="/mySuper/Parameter", value="PowerToolsIsAwesome")  # type: ignore[assignment] # noqa: E501

        return {"mySuperParameterVersion": parameter_version, "statusCode": 200}
    except parameters.exceptions.SetParameterError as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
