from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.utilities import parameters

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    try:
        # set a single parameter, returns the version ID of the parameter
        parameter_version = parameters.set_parameter(name="/mySuper/Parameter", value="PowerToolsIsAwesome")

        return {"mySuperParameterVersion": parameter_version, "statusCode": 200}
    except parameters.exceptions.SetParameterError as error:
        return {"comments": None, "message": str(error), "statusCode": 400}
