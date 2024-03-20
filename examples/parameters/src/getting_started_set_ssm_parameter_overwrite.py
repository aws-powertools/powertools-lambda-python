from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    try:
        # Set a single parameter, but overwrite if it already exists
        # by default, overwrite is False, explicitly set it to True
        updating_parameter = parameters.set_parameter(name="/mySuper/Parameter", value="PowerToolsIsAwesome", overwrite=True)  # type: ignore[assignment] # noqa: E501

        return {"mySuperParameterVersion": updating_parameter, "statusCode": 200}
    except parameters.exceptions.SetParameterError as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
