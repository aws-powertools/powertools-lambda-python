import uuid

from aws_cdk import CfnParameter, CustomResource, Duration, Stack
from aws_cdk.aws_iam import Effect, ManagedPolicy, PolicyStatement, Role, ServicePrincipal
from aws_cdk.aws_lambda import Code, Function, LayerVersion, Runtime
from aws_cdk.aws_logs import RetentionDays
from aws_cdk.aws_ssm import StringParameter
from aws_cdk.custom_resources import Provider
from constructs import Construct


class CanaryStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        powertools_version: str,
        ssm_paramter_layer_arn: str,
        version_tracking_event_bus_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        layer_arn = StringParameter.from_string_parameter_attributes(
            self, "LayerVersionArnParam", parameter_name=ssm_paramter_layer_arn
        ).string_value

        layer = LayerVersion.from_layer_version_arn(self, "PowertoolsLayer", layer_version_arn=layer_arn)
        deploy_stage = CfnParameter(self, "DeployStage", description="Deployment stage for canary").value_as_string

        execution_role = Role(self, "LambdaExecutionRole", assumed_by=ServicePrincipal("lambda.amazonaws.com"))

        execution_role.add_managed_policy(
            ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )

        execution_role.add_to_policy(
            PolicyStatement(effect=Effect.ALLOW, actions=["lambda:GetFunction"], resources=["*"])
        )

        canary_lambda = Function(
            self,
            "CanaryLambdaFunction",
            function_name="CanaryLambdaFunction",
            code=Code.from_asset("layer/canary"),
            handler="app.on_event",
            layers=[layer],
            memory_size=512,
            timeout=Duration.seconds(10),
            runtime=Runtime.PYTHON_3_9,
            log_retention=RetentionDays.ONE_MONTH,
            role=execution_role,
            environment={
                "POWERTOOLS_VERSION": powertools_version,
                "POWERTOOLS_LAYER_ARN": layer_arn,
                "VERSION_TRACKING_EVENT_BUS_ARN": version_tracking_event_bus_arn,
                "LAYER_PIPELINE_STAGE": deploy_stage,
            },
        )

        canary_lambda.add_to_role_policy(
            PolicyStatement(
                effect=Effect.ALLOW, actions=["events:PutEvents"], resources=[version_tracking_event_bus_arn]
            )
        )

        # custom resource provider configuration
        provider = Provider(
            self, "CanaryCustomResource", on_event_handler=canary_lambda, log_retention=RetentionDays.ONE_MONTH
        )
        # force to recreate resource on each deployment with randomized name
        CustomResource(self, f"CanaryTrigger-{str(uuid.uuid4())[0:7]}", service_token=provider.service_token)
