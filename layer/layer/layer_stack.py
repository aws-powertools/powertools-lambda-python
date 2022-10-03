from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk.aws_lambda import Architecture, CfnLayerVersionPermission
from aws_cdk.aws_ssm import StringParameter
from cdk_aws_lambda_powertools_layer import LambdaPowertoolsLayer
from constructs import Construct


class LayerStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        powertools_version: str,
        ssm_paramter_layer_arn: str,
        ssm_parameter_layer_arm64_arn: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        layer = LambdaPowertoolsLayer(
            self,
            "Layer",
            layer_version_name="AWSLambdaPowertoolsPythonV2",
            version=powertools_version,
            include_extras=True,
            compatible_architectures=[Architecture.X86_64()],
        )

        layer_arm64 = LambdaPowertoolsLayer(
            self,
            "Layer-ARM64",
            layer_version_name="AWSLambdaPowertoolsPythonV2-Arm64",
            version=powertools_version,
            include_extras=True,
            compatible_architectures=[Architecture.ARM_64()],
        )

        layer_permission = CfnLayerVersionPermission(
            self,
            "PublicLayerAccess",
            action="lambda:GetLayerVersion",
            layer_version_arn=layer.layer_version_arn,
            principal="*",
        )

        layer_permission_arm64 = CfnLayerVersionPermission(
            self,
            "PublicLayerAccessArm64",
            action="lambda:GetLayerVersion",
            layer_version_arn=layer_arm64.layer_version_arn,
            principal="*",
        )

        layer_permission.apply_removal_policy(RemovalPolicy.RETAIN)
        layer_permission_arm64.apply_removal_policy(RemovalPolicy.RETAIN)

        layer.apply_removal_policy(RemovalPolicy.RETAIN)
        layer_arm64.apply_removal_policy(RemovalPolicy.RETAIN)

        StringParameter(
            self,
            "VersionArn",
            parameter_name=ssm_paramter_layer_arn,
            string_value=layer.layer_version_arn,
        )
        StringParameter(
            self,
            "Arm64VersionArn",
            parameter_name=ssm_parameter_layer_arm64_arn,
            string_value=layer_arm64.layer_version_arn,
        )

        CfnOutput(self, "LatestLayerArn", value=layer.layer_version_arn)
        CfnOutput(self, "LatestLayerArm64Arn", value=layer_arm64.layer_version_arn)
