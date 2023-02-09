import json
from typing import List

from aws_cdk import CfnOutput, Duration
from aws_cdk import aws_appconfig as appconfig
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm
from aws_cdk.aws_lambda import Function

from tests.e2e.utils.data_builder import build_random_value, build_service_name
from tests.e2e.utils.infrastructure import BaseInfrastructure


class ParametersStack(BaseInfrastructure):
    def create_resources(self):
        parameters = self._create_ssm_parameters()

        env_vars = {"parameters": json.dumps(parameters)}
        functions = self.create_lambda_functions(
            function_props={"environment": env_vars, "timeout": Duration.seconds(30)}
        )

        self._create_app_config(function=functions["ParameterAppconfigFreeformHandler"])

        # NOTE: Enforce least-privilege for our param tests only
        functions["ParameterSsmGetParametersByName"].add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameters",
                ],
                resources=[f"arn:aws:ssm:{self.region}:{self.account_id}:parameter/powertools/e2e/parameters/*"],
            )
        )

    def _create_app_config(self, function: Function):
        service_name = build_service_name()

        cfn_application = appconfig.CfnApplication(
            self.stack,
            id="appconfig-app",
            name=f"powertools-e2e-{service_name}",
            description="Lambda Powertools End-to-End testing for AppConfig",
        )
        CfnOutput(self.stack, "AppConfigApplication", value=cfn_application.name)

        cfn_environment = appconfig.CfnEnvironment(
            self.stack,
            "appconfig-env",
            application_id=cfn_application.ref,
            name=f"powertools-e2e{service_name}",
            description="Lambda Powertools End-to-End testing environment",
        )
        CfnOutput(self.stack, "AppConfigEnvironment", value=cfn_environment.name)

        cfn_deployment_strategy = appconfig.CfnDeploymentStrategy(
            self.stack,
            "appconfig-deployment-strategy",
            deployment_duration_in_minutes=0,
            final_bake_time_in_minutes=0,
            growth_factor=100,
            name=f"deploymente2e{service_name}",
            description="deploymente2e",
            replicate_to="NONE",
            growth_type="LINEAR",
        )

        self._create_app_config_freeform(
            app=cfn_application,
            environment=cfn_environment,
            strategy=cfn_deployment_strategy,
            function=function,
            service_name=service_name,
        )

    def _create_app_config_freeform(
        self,
        app: appconfig.CfnApplication,
        environment: appconfig.CfnEnvironment,
        strategy: appconfig.CfnDeploymentStrategy,
        function: Function,
        service_name: str,
    ):
        cfn_configuration_profile = appconfig.CfnConfigurationProfile(
            self.stack,
            "appconfig-profile",
            application_id=app.ref,
            location_uri="hosted",
            type="AWS.Freeform",
            name=f"profilee2e{service_name}",
            description="profilee2e",
        )
        CfnOutput(self.stack, "AppConfigProfile", value=cfn_configuration_profile.name)

        cfn_hosted_configuration_version = appconfig.CfnHostedConfigurationVersion(
            self.stack,
            "appconfig-hosted-deploy",
            application_id=app.ref,
            configuration_profile_id=cfn_configuration_profile.ref,
            content='{"save_history": {"default": true}}',
            content_type="application/json",
            description="hostedconfiguratione2e",
        )
        CfnOutput(self.stack, "AppConfigConfigurationValue", value=cfn_hosted_configuration_version.content)

        appconfig.CfnDeployment(
            self.stack,
            "appconfig-deployment",
            application_id=app.ref,
            configuration_profile_id=cfn_configuration_profile.ref,
            configuration_version=cfn_hosted_configuration_version.ref,
            deployment_strategy_id=strategy.ref,
            environment_id=environment.ref,
            description="deployment",
        )

        function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "appconfig:GetLatestConfiguration",
                    "appconfig:StartConfigurationSession",
                ],
                resources=["*"],
            )
        )

    def _create_ssm_parameters(self) -> List[str]:
        parameters: List[str] = []

        for _ in range(10):
            param = f"/powertools/e2e/parameters/{build_random_value()}"
            rand = build_random_value()
            ssm.StringParameter(self.stack, f"param-{rand}", parameter_name=param, string_value=rand)
            parameters.append(param)

        CfnOutput(self.stack, "ParametersNameList", value=json.dumps(parameters))

        return parameters
