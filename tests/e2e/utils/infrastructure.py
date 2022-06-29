import io
import os
import sys
import zipfile
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple, Type

import boto3
import yaml
from aws_cdk import App, AssetStaging, BundlingOptions, CfnOutput, DockerImage, RemovalPolicy, Stack, aws_logs
from aws_cdk.aws_lambda import Code, Function, LayerVersion, Runtime, Tracing

PYTHON_RUNTIME_VERSION = f"V{''.join(map(str, sys.version_info[:2]))}"


class PythonVersion(Enum):
    V37 = {"runtime": Runtime.PYTHON_3_7, "image": Runtime.PYTHON_3_7.bundling_image.image}
    V38 = {"runtime": Runtime.PYTHON_3_8, "image": Runtime.PYTHON_3_8.bundling_image.image}
    V39 = {"runtime": Runtime.PYTHON_3_9, "image": Runtime.PYTHON_3_9.bundling_image.image}


class InfrastructureStackInterface(ABC):
    @abstractmethod
    def synthesize() -> Tuple[dict, str]:
        ...

    @abstractmethod
    def __call__() -> Tuple[dict, str]:
        ...


class InfrastructureStack(InfrastructureStackInterface):
    def __init__(self, handlers_dir: str, stack_name: str, config: dict) -> None:
        self.stack_name = stack_name
        self.handlers_dir = handlers_dir
        self.config = config

    def _create_layer(self, stack: Stack):
        output_dir = Path(str(AssetStaging.BUNDLING_OUTPUT_DIR), "python")
        input_dir = Path(str(AssetStaging.BUNDLING_INPUT_DIR), "aws_lambda_powertools")
        powertools_layer = LayerVersion(
            stack,
            "aws-lambda-powertools",
            layer_version_name="aws-lambda-powertools",
            compatible_runtimes=[PythonVersion[PYTHON_RUNTIME_VERSION].value["runtime"]],
            code=Code.from_asset(
                path=".",
                bundling=BundlingOptions(
                    image=DockerImage.from_build(
                        str(Path(__file__).parent),
                        build_args={"IMAGE": PythonVersion[PYTHON_RUNTIME_VERSION].value["image"]},
                    ),
                    command=[
                        "bash",
                        "-c",
                        f"poetry export --with-credentials --format requirements.txt --output /tmp/requirements.txt &&\
                            pip install -r /tmp/requirements.txt -t {output_dir} &&\
                            cp -R {input_dir} {output_dir} &&\
                            find {output_dir}/ -regex '^.*__pycache__.*' -delete",
                    ],
                ),
            ),
        )
        return powertools_layer

    def _find_handlers(self, directory: str) -> list:
        for root, _, files in os.walk(directory):
            return [os.path.join(root, filename) for filename in files if filename.endswith(".py")]

    def synthesize(self, handlers: List[str]) -> Tuple[dict, str]:
        integration_test_app = App()
        stack = Stack(integration_test_app, self.stack_name)
        powertools_layer = self._create_layer(stack)
        code = Code.from_asset(self.handlers_dir)

        for filename_path in handlers:
            filename = Path(filename_path).stem
            function_python = Function(
                stack,
                f"{filename}-lambda",
                runtime=PythonVersion[PYTHON_RUNTIME_VERSION].value["runtime"],
                code=code,
                handler=f"{filename}.lambda_handler",
                layers=[powertools_layer],
                environment=self.config.get("environment_variables"),
                tracing=Tracing.ACTIVE
                if self.config.get("parameters", {}).get("tracing") == "ACTIVE"
                else Tracing.DISABLED,
            )

            aws_logs.LogGroup(
                stack,
                f"{filename}-lg",
                log_group_name=f"/aws/lambda/{function_python.function_name}",
                retention=aws_logs.RetentionDays.ONE_DAY,
                removal_policy=RemovalPolicy.DESTROY,
            )
            CfnOutput(stack, f"{filename}_arn", value=function_python.function_arn)
        return (
            integration_test_app.synth().get_stack_by_name(self.stack_name).template,
            integration_test_app.synth().directory,
        )

    def __call__(self) -> Tuple[dict, str]:
        handlers = self._find_handlers(directory=self.handlers_dir)
        return self.synthesize(handlers=handlers)


class Infrastructure:
    def __init__(self, stack_name: str, handlers_dir: str, config: dict) -> None:
        session = boto3.Session()
        self.s3_client = session.client("s3")
        self.lambda_client = session.client("lambda")
        self.cf_client = session.client("cloudformation")
        self.s3_resource = session.resource("s3")
        self.account_id = session.client("sts").get_caller_identity()["Account"]
        self.region = session.region_name
        self.stack_name = stack_name
        self.handlers_dir = handlers_dir
        self.config = config

    def deploy(self, Stack: Type[InfrastructureStackInterface]) -> Dict[str, str]:

        stack = Stack(handlers_dir=self.handlers_dir, stack_name=self.stack_name, config=self.config)
        template, asset_root_dir = stack()
        self._upload_assets(template, asset_root_dir)

        response = self._deploy_stack(self.stack_name, template)

        return self._transform_output(response["Stacks"][0]["Outputs"])

    def delete(self):
        self.cf_client.delete_stack(StackName=self.stack_name)

    def _upload_assets(self, template: dict, asset_root_dir: str):

        assets = self._find_assets(template, self.account_id, self.region)

        for s3_key, bucket in assets.items():
            s3_bucket = self.s3_resource.Bucket(bucket)
            if bool(list(s3_bucket.objects.filter(Prefix=s3_key))):
                print("object exists, skipping")
                continue

            buf = io.BytesIO()
            asset_dir = f"{asset_root_dir}/asset.{Path(s3_key).with_suffix('')}"
            os.chdir(asset_dir)
            asset_files = self._find_files(directory=".")
            with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for asset_file in asset_files:
                    zf.write(os.path.join(asset_file))
            buf.seek(0)
            self.s3_client.upload_fileobj(Fileobj=buf, Bucket=bucket, Key=s3_key)

    def _find_files(self, directory: str) -> list:
        file_paths = []
        for root, _, files in os.walk(directory):
            for filename in files:
                file_paths.append(os.path.join(root, filename))
        return file_paths

    def _deploy_stack(self, stack_name: str, template: dict):
        response = self.cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=yaml.dump(template),
            TimeoutInMinutes=10,
            OnFailure="ROLLBACK",
            Capabilities=["CAPABILITY_IAM"],
        )
        waiter = self.cf_client.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name, WaiterConfig={"Delay": 10, "MaxAttempts": 50})
        response = self.cf_client.describe_stacks(StackName=stack_name)
        return response

    def _find_assets(self, template: dict, account_id: str, region: str):
        assets = {}
        for _, resource in template["Resources"].items():
            bucket = None
            S3Key = None

            if resource["Properties"].get("Code"):
                bucket = resource["Properties"]["Code"]["S3Bucket"]
                S3Key = resource["Properties"]["Code"]["S3Key"]
            elif resource["Properties"].get("Content"):
                bucket = resource["Properties"]["Content"]["S3Bucket"]
                S3Key = resource["Properties"]["Content"]["S3Key"]
            if S3Key and bucket:
                assets[S3Key] = (
                    bucket["Fn::Sub"].replace("${AWS::AccountId}", account_id).replace("${AWS::Region}", region)
                )

        return assets

    def _transform_output(self, outputs: dict):
        return {output["OutputKey"]: output["OutputValue"] for output in outputs if output["OutputKey"]}
