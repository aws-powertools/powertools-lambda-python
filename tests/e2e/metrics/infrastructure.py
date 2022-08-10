from pathlib import Path
from typing import TYPE_CHECKING, Dict, Tuple
from uuid import uuid4

import boto3
import yaml
from aws_cdk import App, CfnOutput, RemovalPolicy, Stack, aws_logs
from aws_cdk.aws_lambda import Code, Function, LayerVersion, Runtime, Tracing

from tests.e2e.utils.asset import Assets

if TYPE_CHECKING:
    from mypy_boto3_cloudformation import CloudFormationClient


class MetricsStack:
    def __init__(self, handlers_dir: Path) -> None:
        self.stack_name = f"test-metrics-{uuid4()}"
        self.handlers_dir = handlers_dir  # hardcoded as we're not using a fixture yet
        self.app = App()
        self.stack = Stack(self.app, self.stack_name)
        self.session = boto3.Session()
        self.cf_client: "CloudFormationClient" = self.session.client("cloudformation")
        # NOTE: CDK stack account and region are tokens, we need to resolve earlier
        self.account_id = self.session.client("sts").get_caller_identity()["Account"]
        self.region = self.session.region_name
        self.stack_outputs: Dict[str, str] = {}

    def create_functions(self):
        handlers = list(self.handlers_dir.rglob("*.py"))
        source = Code.from_asset(f"{self.handlers_dir}")
        for fn in handlers:
            fn_name = fn.stem
            function_python = Function(
                self.stack,
                id=f"{fn_name}-lambda",
                runtime=Runtime.PYTHON_3_8,
                code=source,
                handler=f"{fn_name}.lambda_handler",
                tracing=Tracing.ACTIVE,
                layers=[
                    LayerVersion.from_layer_version_arn(
                        self.stack,
                        "lambda-powertools",
                        f"arn:aws:lambda:{self.region}:017000801446:layer:AWSLambdaPowertoolsPython:29",
                    )
                ],
            )

            aws_logs.LogGroup(
                self.stack,
                id=f"{fn_name}-lg",
                log_group_name=f"/aws/lambda/{function_python.function_name}",
                retention=aws_logs.RetentionDays.ONE_DAY,
                removal_policy=RemovalPolicy.DESTROY,
            )

            # CFN Outputs only support hyphen
            fn_name_camel_case = fn_name.title().replace("_", "")  # basic_handler -> BasicHandler
            CfnOutput(self.stack, f"{fn_name_camel_case}Arn", value=function_python.function_arn)

    def deploy(self) -> Dict[str, str]:
        """Creates CloudFormation Stack and return stack outputs as dict

        Returns
        -------
        Dict[str, str]
            CloudFormation Stack Outputs with output key and value
        """
        template, asset_manifest_file = self._synthesize()
        assets = Assets(cfn_template=asset_manifest_file, account_id=self.account_id, region=self.region)
        assets.upload()
        return self._deploy_stack(self.stack_name, template)

    def delete(self):
        self.cf_client.delete_stack(StackName=self.stack_name)

    def _synthesize(self) -> Tuple[Dict, Path]:
        self.create_functions()
        cloud_assembly = self.app.synth()
        cf_template: Dict = cloud_assembly.get_stack_by_name(self.stack_name).template
        cloud_assembly_assets_manifest_path: str = (
            cloud_assembly.get_stack_by_name(self.stack_name).dependencies[0].file
        )
        return cf_template, Path(cloud_assembly_assets_manifest_path)

    def _deploy_stack(self, stack_name: str, template: Dict) -> Dict[str, str]:
        self.cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=yaml.dump(template),
            TimeoutInMinutes=10,
            OnFailure="ROLLBACK",
            Capabilities=["CAPABILITY_IAM"],
        )
        waiter = self.cf_client.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name, WaiterConfig={"Delay": 10, "MaxAttempts": 50})

        stack_details = self.cf_client.describe_stacks(StackName=stack_name)
        stack_outputs = stack_details["Stacks"][0]["Outputs"]
        self.stack_outputs = {
            output["OutputKey"]: output["OutputValue"] for output in stack_outputs if output["OutputKey"]
        }

        return self.stack_outputs

    def get_stack_outputs(self) -> Dict[str, str]:
        return self.stack_outputs
