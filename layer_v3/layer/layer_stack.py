from __future__ import annotations

import jsii
from aws_cdk import (
    Aspects,
    CfnCondition,
    CfnOutput,
    CfnParameter,
    CfnResource,
    Fn,
    IAspect,
    RemovalPolicy,
    Stack,
)
from aws_cdk.aws_lambda import Architecture, CfnLayerVersionPermission, Runtime
from aws_cdk.aws_ssm import StringParameter
from constructs import Construct

from layer_v3.layer_constructors.layer_stack import LambdaPowertoolsLayerPythonV3


@jsii.implements(IAspect)
class ApplyCondition:
    def __init__(self, condition: CfnCondition):
        self.condition = condition

    def visit(self, node):
        if isinstance(node, CfnResource):
            node.cfn_options.condition = self.condition
        if isinstance(node, CfnOutput):
            node.condition = self.condition


class Layer(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        layer_version_name: str,
        powertools_version: str,
        python_version: str,
        architecture: Architecture | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        layer = LambdaPowertoolsLayerPythonV3(
            self,
            "Layer",
            layer_name=layer_version_name,
            powertools_version=powertools_version,
            python_version=python_version,
            include_extras=True,
            architecture=architecture or Architecture.X86_64,
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
        python_version: str,
        ssm_parameter_layer_arn: str,
        ssm_parameter_layer_arm64_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        python_version_normalized = python_version.replace(".", "")
        layer_name_x86_64 = f"AWSLambdaPowertoolsPythonV3-{python_version_normalized}-x86_64"
        layer_name_arm64 = f"AWSLambdaPowertoolsPythonV3-{python_version_normalized}-arm64"

        if python_version == "python3.8":
            python_version = Runtime.PYTHON_3_8
        if python_version == "python3.9":
            python_version = Runtime.PYTHON_3_9
        if python_version == "python3.10":
            python_version = Runtime.PYTHON_3_10
        if python_version == "python3.11":
            python_version = Runtime.PYTHON_3_11
        if python_version == "python3.12":
            python_version = Runtime.PYTHON_3_12

        has_arm64_support = CfnParameter(
            self,
            "HasARM64Support",
            description="Has ARM64 Support Condition",
            type="String",
            allowed_values=["true", "false"],
        )

        has_arm64_condition = CfnCondition(
            self,
            "HasARM64SupportCondition",
            expression=Fn.condition_equals(has_arm64_support, "true"),
        )
        has_no_arm64_condition = CfnCondition(
            self,
            "HasNOArm64SupportCondition",
            expression=Fn.condition_equals(has_arm64_support, "false"),
        )

        # The following code is used when the region does not support ARM64 Lambdas. We make sure to only create the
        # X86_64 Layer without specifying any compatible architecture, which would result in a CloudFormation error.

        layer_single = Layer(
            self,
            f"LayerSingle-{python_version_normalized}",
            layer_version_name=layer_name_x86_64,
            python_version=python_version,
            powertools_version=powertools_version,
        )
        Aspects.of(layer_single).add(ApplyCondition(has_no_arm64_condition))

        Aspects.of(
            StringParameter(
                self,
                f"SingleVersionArn-{python_version_normalized}",
                parameter_name=ssm_parameter_layer_arn,
                string_value=layer_single.layer_version_arn,
            ),
        ).add(ApplyCondition(has_no_arm64_condition))

        # The following code is used when the region has support for ARM64 Lambdas. In this case, we explicitly
        # create a Layer for both X86_64 and ARM64, specifying the compatible architectures.

        # X86_64 layer

        layer = Layer(
            self,
            f"Layer-{python_version_normalized}",
            layer_version_name=layer_name_x86_64,
            powertools_version=powertools_version,
            python_version=python_version,
            architecture=Architecture.X86_64,
        )
        Aspects.of(layer).add(ApplyCondition(has_arm64_condition))

        Aspects.of(
            StringParameter(
                self,
                f"VersionArn-{python_version_normalized}",
                parameter_name=ssm_parameter_layer_arn,
                string_value=layer.layer_version_arn,
            ),
        ).add(ApplyCondition(has_arm64_condition))

        CfnOutput(
            self,
            "LatestLayerArn",
            value=Fn.condition_if(
                has_arm64_condition.logical_id,
                layer.layer_version_arn,
                layer_single.layer_version_arn,
            ).to_string(),
        )

        # ARM64 layer

        layer_arm64 = Layer(
            self,
            f"Layer-ARM64-{python_version_normalized}",
            layer_version_name=layer_name_arm64,
            powertools_version=powertools_version,
            python_version=python_version,
            architecture=Architecture.ARM_64,
        )
        Aspects.of(layer_arm64).add(ApplyCondition(has_arm64_condition))

        StringParameter(
            self,
            f"Arm64VersionArn-{python_version_normalized}",
            parameter_name=ssm_parameter_layer_arm64_arn,
            string_value=Fn.condition_if(
                has_arm64_condition.logical_id,
                layer_arm64.layer_version_arn,
                "none",
            ).to_string(),
        )

        Aspects.of(CfnOutput(self, "LatestLayerArm64Arn", value=layer_arm64.layer_version_arn)).add(
            ApplyCondition(has_arm64_condition),
        )
