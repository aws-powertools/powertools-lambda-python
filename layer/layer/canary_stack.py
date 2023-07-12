import uuid

import jsii
from aws_cdk import (
    Aspects,
    CfnCondition,
    CfnParameter,
    CfnResource,
    CustomResource,
    Duration,
    Fn,
    IAspect,
    Stack,
)
from aws_cdk.aws_iam import (
    Effect,
    ManagedPolicy,
    PolicyStatement,
    Role,
    ServicePrincipal,
)
from aws_cdk.aws_lambda import Architecture, Code, Function, LayerVersion, Runtime
from aws_cdk.aws_logs import RetentionDays
from aws_cdk.aws_ssm import StringParameter
from aws_cdk.custom_resources import Provider
from constructs import Construct

VERSION_TRACKING_EVENT_BUS_ARN: str = (
    "arn:aws:events:eu-central-1:027876851704:event-bus/VersionTrackingEventBus"
)


@jsii.implements(IAspect)
class ApplyCondition:
    def __init__(self, condition: CfnCondition):
        self.condition = condition

    def visit(self, node):
        if isinstance(node, CfnResource):
            node.cfn_options.condition = self.condition


class CanaryStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        powertools_version: str,
        ssm_paramter_layer_arn: str,
        ssm_parameter_layer_arm64_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        deploy_stage = CfnParameter(
            self, "DeployStage", description="Deployment stage for canary"
        ).value_as_string

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

        layer_arn = StringParameter.from_string_parameter_attributes(
            self, "LayerVersionArnParam", parameter_name=ssm_paramter_layer_arn
        ).string_value
        Canary(
            self,
            "Canary-x86-64",
            layer_arn=layer_arn,
            powertools_version=powertools_version,
            architecture=Architecture.X86_64,
            stage=deploy_stage,
        )

        layer_arm64_arn = StringParameter.from_string_parameter_attributes(
            self,
            "LayerArm64VersionArnParam",
            parameter_name=ssm_parameter_layer_arm64_arn,
        ).string_value

        arm64_canary = Canary(
            self,
            "Canary-arm64",
            layer_arn=layer_arm64_arn,
            powertools_version=powertools_version,
            architecture=Architecture.ARM_64,
            stage=deploy_stage,
        )
        Aspects.of(arm64_canary).add(ApplyCondition(has_arm64_condition))


class Canary(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        layer_arn: str,
        powertools_version: str,
        architecture: Architecture,
        stage: str,
    ):
        super().__init__(scope, construct_id)

        layer = LayerVersion.from_layer_version_arn(
            self, "PowertoolsLayer", layer_version_arn=layer_arn
        )

        execution_role = Role(
            self,
            "LambdaExecutionRole",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"),
        )

        execution_role.add_managed_policy(
            ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )

        execution_role.add_to_policy(
            PolicyStatement(
                effect=Effect.ALLOW, actions=["lambda:GetFunction"], resources=["*"]
            )
        )

        canary_lambda = Function(
            self,
            "CanaryLambdaFunction",
            code=Code.from_asset("layer/canary"),
            handler="app.on_event",
            layers=[layer],
            memory_size=512,
            timeout=Duration.seconds(10),
            runtime=Runtime.PYTHON_3_9,
            architecture=architecture,
            log_retention=RetentionDays.ONE_MONTH,
            role=execution_role,
            environment={
                "POWERTOOLS_VERSION": powertools_version,
                "POWERTOOLS_LAYER_ARN": layer_arn,
                "VERSION_TRACKING_EVENT_BUS_ARN": VERSION_TRACKING_EVENT_BUS_ARN,
                "LAYER_PIPELINE_STAGE": stage,
            },
        )

        canary_lambda.add_to_role_policy(
            PolicyStatement(
                effect=Effect.ALLOW,
                actions=["events:PutEvents"],
                resources=[VERSION_TRACKING_EVENT_BUS_ARN],
            )
        )

        # custom resource provider configuration
        provider = Provider(
            self,
            "CanaryCustomResource",
            on_event_handler=canary_lambda,
            log_retention=RetentionDays.ONE_MONTH,
        )
        # force to recreate resource on each deployment with randomized name
        CustomResource(
            self,
            f"CanaryTrigger-{str(uuid.uuid4())[0:7]}",
            service_token=provider.service_token,
        )
