from typing import Any

from aws_cdk import CfnOutput
from aws_cdk import aws_ssm as ssm

from tests.e2e.utils.infrastructure import BaseInfrastructure


class ParametersStack(BaseInfrastructure):
    def create_resources(self):
        functions = self.create_lambda_functions()
        self._create_parameter_string(function=functions)

    def _create_parameter_string(self, function: Any):
        parameter = ssm.StringParameter(
            self.stack, id="string_parameter", parameter_name="sample_string", string_value="Lambda Powertools"
        )

        parameter.grant_read(function["ParameterStringHandler"])

        CfnOutput(self.stack, "ParameterString", value=parameter.parameter_name)
