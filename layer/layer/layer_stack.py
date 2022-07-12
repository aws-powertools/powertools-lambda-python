from aws_cdk import Stack
from aws_cdk.aws_ssm import StringParameter
from cdk_lambda_powertools_python_layer import LambdaPowertoolsLayer
from constructs import Construct


class LayerStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, powertools_version: str, ssm_paramter_layer_arn: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        layer = LambdaPowertoolsLayer(
            self, "Layer", layer_version_name="AWSLambdaPowertoolsPython", version=powertools_version
        )

        layer.add_permission("PublicLayerAccess", account_id="*")

        StringParameter(self, "VersionArn", parameter_name=ssm_paramter_layer_arn, string_value=layer.layer_version_arn)
