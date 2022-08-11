import io
import json
import os
import sys
import zipfile
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Type
from uuid import uuid4

import boto3
import yaml
from aws_cdk import App, AssetStaging, BundlingOptions, CfnOutput, DockerImage, RemovalPolicy, Stack, aws_logs
from aws_cdk.aws_lambda import Code, Function, LayerVersion, Runtime, Tracing
from mypy_boto3_cloudformation import CloudFormationClient

from tests.e2e.utils.asset import Assets

PYTHON_RUNTIME_VERSION = f"V{''.join(map(str, sys.version_info[:2]))}"


class PythonVersion(Enum):
    V37 = {"runtime": Runtime.PYTHON_3_7, "image": Runtime.PYTHON_3_7.bundling_image.image}
    V38 = {"runtime": Runtime.PYTHON_3_8, "image": Runtime.PYTHON_3_8.bundling_image.image}
    V39 = {"runtime": Runtime.PYTHON_3_9, "image": Runtime.PYTHON_3_9.bundling_image.image}


class BaseInfrastructureStack(ABC):
    @abstractmethod
    def synthesize(self) -> Tuple[dict, str]:
        ...

    @abstractmethod
    def __call__(self) -> Tuple[dict, str]:
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
        self.cfn = session.client("cloudformation")
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
        self.cfn.delete_stack(StackName=self.stack_name)

    def _upload_assets(self, asset_root_dir: str, asset_manifest_file: str):
        """
        This method is drop-in replacement for cdk-assets package s3 upload part.
        https://www.npmjs.com/package/cdk-assets.
        We use custom solution to avoid dependencies from nodejs ecosystem.
        We follow the same design cdk-assets:
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
        response = self.cfn.create_stack(
            StackName=stack_name,
            TemplateBody=yaml.dump(template),
            TimeoutInMinutes=10,
            OnFailure="ROLLBACK",
            Capabilities=["CAPABILITY_IAM"],
        )
        waiter = self.cfn.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name, WaiterConfig={"Delay": 10, "MaxAttempts": 50})
        response = self.cfn.describe_stacks(StackName=stack_name)
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


class BaseInfrastructureV2(ABC):
    def __init__(self, feature_name: str, handlers_dir: Path) -> None:
        self.stack_name = f"test-{feature_name}-{uuid4()}"
        self.handlers_dir = handlers_dir
        self.stack_outputs: Dict[str, str] = {}
        self.app = App()
        self.stack = Stack(self.app, self.stack_name)
        self.session = boto3.Session()
        self.cfn: CloudFormationClient = self.session.client("cloudformation")

        # NOTE: CDK stack account and region are tokens, we need to resolve earlier
        self.account_id = self.session.client("sts").get_caller_identity()["Account"]
        self.region = self.session.region_name

    def create_lambda_functions(self, function_props: Optional[Dict] = None):
        """Create Lambda functions available under handlers_dir

        It creates CloudFormation Outputs for every function found in PascalCase. For example,
        {handlers_dir}/basic_handler.py creates `BasicHandler` and `BasicHandlerArn` outputs.


        Parameters
        ----------
        function_props: Optional[Dict]
            CDK Lambda FunctionProps as dictionary to override defaults

        Examples
        --------

        Creating Lambda functions available in the handlers directory

        ```python
        self.create_lambda_functions()
        ```

        Creating Lambda functions and override runtime to Python 3.7

        ```python
        from aws_cdk.aws_lambda import Runtime

        self.create_lambda_functions(function_props={"runtime": Runtime.PYTHON_3_7)
        ```
        """
        handlers = list(self.handlers_dir.rglob("*.py"))
        source = Code.from_asset(f"{self.handlers_dir}")
        props_override = function_props or {}

        for fn in handlers:
            fn_name = fn.stem
            function_settings = {
                "id": f"{fn_name}-lambda",
                "code": source,
                "handler": f"{fn_name}.lambda_handler",
                "tracing": Tracing.ACTIVE,
                "runtime": Runtime.PYTHON_3_9,
                "layers": [
                    LayerVersion.from_layer_version_arn(
                        self.stack,
                        f"{fn_name}-lambda-powertools",
                        f"arn:aws:lambda:{self.region}:017000801446:layer:AWSLambdaPowertoolsPython:29",
                    )
                ],
                **props_override,
            }

            function_python = Function(self.stack, **function_settings)

            aws_logs.LogGroup(
                self.stack,
                id=f"{fn_name}-lg",
                log_group_name=f"/aws/lambda/{function_python.function_name}",
                retention=aws_logs.RetentionDays.ONE_DAY,
                removal_policy=RemovalPolicy.DESTROY,
            )

            # CFN Outputs only support hyphen
            fn_name_pascal_case = fn_name.title().replace("_", "")  # basic_handler -> BasicHandler
            self._add_resource_output(
                name=fn_name_pascal_case, value=function_python.function_name, arn=function_python.function_arn
            )

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
        """Delete CloudFormation Stack"""
        self.cfn.delete_stack(StackName=self.stack_name)

    @abstractmethod
    def create_resources(self):
        """Create any necessary CDK resources. It'll be called before deploy

        Examples
        -------

        Creating a S3 bucket and export name and ARN

        ```python
        def created_resources(self):
            s3 = s3.Bucket(self.stack, "MyBucket")

            # This will create MyBucket and MyBucketArn CloudFormation Output
            self._add_resource_output(name="MyBucket", value=s3.bucket_name, arn_value=bucket.bucket_arn)
        ```

        Creating Lambda functions available in the handlers directory

        ```python
        def created_resources(self):
            self.create_lambda_functions()
        ```
        """
        ...

    def _synthesize(self) -> Tuple[Dict, Path]:
        self.create_resources()
        cloud_assembly = self.app.synth()
        cf_template: Dict = cloud_assembly.get_stack_by_name(self.stack_name).template
        cloud_assembly_assets_manifest_path: str = (
            cloud_assembly.get_stack_by_name(self.stack_name).dependencies[0].file  # type: ignore[attr-defined]
        )
        return cf_template, Path(cloud_assembly_assets_manifest_path)

    def _deploy_stack(self, stack_name: str, template: Dict) -> Dict[str, str]:
        self.cfn.create_stack(
            StackName=stack_name,
            TemplateBody=yaml.dump(template),
            TimeoutInMinutes=10,
            OnFailure="ROLLBACK",
            Capabilities=["CAPABILITY_IAM"],
        )
        waiter = self.cfn.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name, WaiterConfig={"Delay": 10, "MaxAttempts": 50})

        stack_details = self.cfn.describe_stacks(StackName=stack_name)
        stack_outputs = stack_details["Stacks"][0]["Outputs"]
        self.stack_outputs = {
            output["OutputKey"]: output["OutputValue"] for output in stack_outputs if output["OutputKey"]
        }

        return self.stack_outputs

    def _add_resource_output(self, name: str, value: str, arn: str):
        """Add both resource value and ARN as Outputs to facilitate tests.

        This will create two outputs: {Name} and {Name}Arn

        Parameters
        ----------
        name : str
            CloudFormation Output Key
        value : str
            CloudFormation Output Value
        arn : str
            CloudFormation Output Value for ARN
        """
        CfnOutput(self.stack, f"{name}", value=value)
        CfnOutput(self.stack, f"{name}Arn", value=arn)
