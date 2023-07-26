from typing import Optional

from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
)
from aws_cdk.aws_ssm import StringParameter
from aws_cdk.aws_lambda import Architecture, CfnLayerVersionPermission
from cdk_aws_lambda_powertools_layer import LambdaPowertoolsLayer
from constructs import Construct


class Layer(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        layer_version_name: str,
        powertools_version: str,
        architecture: Optional[Architecture] = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        layer = LambdaPowertoolsLayer(
            self,
            "Layer",
            layer_version_name=layer_version_name,
            version=powertools_version,
            include_extras=True,
            compatible_architectures=[architecture] if architecture else [],
        )
        layer.apply_removal_policy(RemovalPolicy.RETAIN)

        self.layer_version_arn = layer.layer_version_arn

        layer_permission = CfnLayerVersionPermission(
            self,
            "PublicLayerAccess",
            action="lambda:GetLayerVersion",
            layer_version_arn=layer.layer_version_arn,
            principal="*",
        )
        layer_permission.apply_removal_policy(RemovalPolicy.RETAIN)


class LayerStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        powertools_version: str,
        ssm_parameter_layer_arn: str,
        architecture: Architecture,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        layer_name = (
            "AWSLambdaPowertoolsPythonV2"
            if architecture.to_string() == "x86_64"
            else "AWSLambdaPowertoolsPythonV2-Arm64"
        )

        layer = Layer(
            self,
            "Layer",
            layer_version_name=layer_name,
            powertools_version=powertools_version,
            architecture=architecture,
        )

        StringParameter(
            self,
            "VersionArn",
            parameter_name=ssm_parameter_layer_arn,
            string_value=layer.layer_version_arn,
        )

        CfnOutput(self, "LatestLayerArn", value=layer.layer_version_arn)
