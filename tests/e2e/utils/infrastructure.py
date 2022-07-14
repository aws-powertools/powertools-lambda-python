import io
import json
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


class BaseInfrastructureStack(ABC):
    @abstractmethod
    def synthesize() -> Tuple[dict, str]:
        ...

    @abstractmethod
    def __call__() -> Tuple[dict, str]:
        ...


class InfrastructureStack(BaseInfrastructureStack):
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
                        rf"poetry export --with-credentials --format requirements.txt --output /tmp/requirements.txt &&\
                            pip install -r /tmp/requirements.txt -t {output_dir} &&\
                            cp -R {input_dir} {output_dir}",
                    ],
                ),
            ),
        )
        return powertools_layer

    def _find_handlers(self, directory: str) -> List:
        for root, _, files in os.walk(directory):
            return [os.path.join(root, filename) for filename in files if filename.endswith(".py")]

    def synthesize(self, handlers: List[str]) -> Tuple[dict, str, str]:
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
        cloud_assembly = integration_test_app.synth()
        cf_template = cloud_assembly.get_stack_by_name(self.stack_name).template
        cloud_assembly_directory = cloud_assembly.directory
        cloud_assembly_assets_manifest_path = cloud_assembly.get_stack_by_name(self.stack_name).dependencies[0].file

        return (cf_template, cloud_assembly_directory, cloud_assembly_assets_manifest_path)

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

    def deploy(self, Stack: Type[BaseInfrastructureStack]) -> Dict[str, str]:

        stack = Stack(handlers_dir=self.handlers_dir, stack_name=self.stack_name, config=self.config)
        template, asset_root_dir, asset_manifest_file = stack()
        self._upload_assets(asset_root_dir, asset_manifest_file)

        response = self._deploy_stack(self.stack_name, template)

        return self._transform_output(response["Stacks"][0]["Outputs"])

    def delete(self):
        self.cf_client.delete_stack(StackName=self.stack_name)

    def _upload_assets(self, asset_root_dir: str, asset_manifest_file: str):
        """
        This method is drop-in replacement for cdk-assets package s3 upload part.
        https://www.npmjs.com/package/cdk-assets.
        We use custom solution to avoid dependencies from nodejs ecosystem.
        We follow the same design cdk-assets follows:
        https://github.com/aws/aws-cdk-rfcs/blob/master/text/0092-asset-publishing.md.
        """

        assets = self._find_assets(asset_manifest_file, self.account_id, self.region)

        for s3_key, config in assets.items():
            print(config)
            s3_bucket = self.s3_resource.Bucket(config["bucket_name"])

            if config["asset_packaging"] != "zip":
                print("Asset is not a zip file. Skipping upload")
                continue

            if bool(list(s3_bucket.objects.filter(Prefix=s3_key))):
                print("object exists, skipping")
                continue

            buf = io.BytesIO()
            asset_dir = f"{asset_root_dir}/{config['asset_path']}"
            os.chdir(asset_dir)
            asset_files = self._find_files(directory=".")
            with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for asset_file in asset_files:
                    zf.write(os.path.join(asset_file))
            buf.seek(0)
            self.s3_client.upload_fileobj(Fileobj=buf, Bucket=config["bucket_name"], Key=s3_key)

    def _find_files(self, directory: str) -> List:
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

    def _find_assets(self, asset_template: str, account_id: str, region: str):
        assets = {}
        with open(asset_template, mode="r") as template:
            for _, config in json.loads(template.read())["files"].items():
                asset_path = config["source"]["path"]
                asset_packaging = config["source"]["packaging"]
                bucket_name = config["destinations"]["current_account-current_region"]["bucketName"]
                object_key = config["destinations"]["current_account-current_region"]["objectKey"]

                assets[object_key] = {
                    "bucket_name": bucket_name.replace("${AWS::AccountId}", account_id).replace(
                        "${AWS::Region}", region
                    ),
                    "asset_path": asset_path,
                    "asset_packaging": asset_packaging,
                }

        return assets

    def _transform_output(self, outputs: dict):
        return {output["OutputKey"]: output["OutputValue"] for output in outputs if output["OutputKey"]}
