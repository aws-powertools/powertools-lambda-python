import json
import logging
import os
import subprocess
import sys
import textwrap
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, Generator, Optional, Tuple, Type
from uuid import uuid4

import boto3
import pytest
from aws_cdk import (
    App,
    AssetStaging,
    BundlingOptions,
    CfnOutput,
    DockerImage,
    Environment,
    RemovalPolicy,
    Stack,
    aws_logs,
)
from aws_cdk.aws_lambda import Code, Function, LayerVersion, Runtime, Tracing
from filelock import FileLock
from mypy_boto3_cloudformation import CloudFormationClient

from aws_lambda_powertools import PACKAGE_PATH

PYTHON_RUNTIME_VERSION = f"V{''.join(map(str, sys.version_info[:2]))}"
SOURCE_CODE_ROOT_PATH = PACKAGE_PATH.parent
CDK_OUT_PATH = SOURCE_CODE_ROOT_PATH / "cdk.out"

logger = logging.getLogger(__name__)


class BaseInfrastructureStack(ABC):
    @abstractmethod
    def synthesize(self) -> Tuple[dict, str]:
        ...

    @abstractmethod
    def __call__(self) -> Tuple[dict, str]:
        ...


class PythonVersion(Enum):
    V37 = {"runtime": Runtime.PYTHON_3_7, "image": Runtime.PYTHON_3_7.bundling_image.image}
    V38 = {"runtime": Runtime.PYTHON_3_8, "image": Runtime.PYTHON_3_8.bundling_image.image}
    V39 = {"runtime": Runtime.PYTHON_3_9, "image": Runtime.PYTHON_3_9.bundling_image.image}


class BaseInfrastructure(ABC):
    RANDOM_STACK_VALUE: str = f"{uuid4()}"

    def __init__(self, feature_name: str, handlers_dir: Path, layer_arn: str = "") -> None:
        self.feature_name = feature_name
        self.stack_name = f"test{PYTHON_RUNTIME_VERSION}-{feature_name}-{self.RANDOM_STACK_VALUE}"
        self.handlers_dir = handlers_dir
        self.layer_arn = layer_arn
        self.stack_outputs: Dict[str, str] = {}
        self.stack_outputs_file = f"{CDK_OUT_PATH / self.feature_name}_stack_outputs.json"  # tracer_stack_outputs.json

        # NOTE: CDK stack account and region are tokens, we need to resolve earlier
        self.session = boto3.Session()
        self.cfn: CloudFormationClient = self.session.client("cloudformation")
        self.account_id = self.session.client("sts").get_caller_identity()["Account"]
        self.region = self.session.region_name

        self.app = App()
        self.stack = Stack(self.app, self.stack_name, env=Environment(account=self.account_id, region=self.region))

    def create_lambda_functions(self, function_props: Optional[Dict] = None) -> Dict[str, Function]:
        """Create Lambda functions available under handlers_dir

        It creates CloudFormation Outputs for every function found in PascalCase. For example,
        {handlers_dir}/basic_handler.py creates `BasicHandler` and `BasicHandlerArn` outputs.


        Parameters
        ----------
        function_props: Optional[Dict]
            Dictionary representing CDK Lambda FunctionProps to override defaults

        Returns
        -------
        output: Dict[str, Function]
            A dict with PascalCased function names and the corresponding CDK Function object

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
        logger.debug(f"Creating functions for handlers: {handlers}")
        if not self.layer_arn:
            raise ValueError(
                """Lambda Layer ARN cannot be empty when creating Lambda functions.
                Make sure to inject `lambda_layer_arn` fixture and pass at the constructor level"""
            )

        layer = LayerVersion.from_layer_version_arn(self.stack, "layer-arn", layer_version_arn=self.layer_arn)
        function_settings_override = function_props or {}
        output: Dict[str, Function] = {}

        for fn in handlers:
            fn_name = fn.stem
            fn_name_pascal_case = fn_name.title().replace("_", "")  # basic_handler -> BasicHandler
            logger.debug(f"Creating function: {fn_name_pascal_case}")
            function_settings = {
                "id": f"{fn_name}-lambda",
                "code": source,
                "handler": f"{fn_name}.lambda_handler",
                "tracing": Tracing.ACTIVE,
                "runtime": Runtime.PYTHON_3_9,
                "layers": [layer],
                **function_settings_override,
            }

            function = Function(self.stack, **function_settings)

            aws_logs.LogGroup(
                self.stack,
                id=f"{fn_name}-lg",
                log_group_name=f"/aws/lambda/{function.function_name}",
                retention=aws_logs.RetentionDays.ONE_DAY,
                removal_policy=RemovalPolicy.DESTROY,
            )

            # CFN Outputs only support hyphen hence pascal case
            self.add_cfn_output(name=fn_name_pascal_case, value=function.function_name, arn=function.function_arn)

            output[fn_name_pascal_case] = function

        return output

    def deploy(self) -> Dict[str, str]:
        """Synthesize and deploy a CDK app, and return its stack outputs

        NOTE: It auto-generates a temporary CDK app to benefit from CDK CLI lookup features

        Returns
        -------
        Dict[str, str]
            CloudFormation Stack Outputs with output key and value
        """
        cdk_app_file = self._create_temp_cdk_app()
        self.stack_outputs = self._deploy_stack(cdk_app_file)
        return self.stack_outputs

    def delete(self) -> None:
        """Delete CloudFormation Stack"""
        logger.debug(f"Deleting stack: {self.stack_name}")
        self.cfn.delete_stack(StackName=self.stack_name)

    def _deploy_stack(self, cdk_app_file: str) -> Dict:
        """Deploys CDK App auto-generated using CDK CLI

        Parameters
        ----------
        cdk_app_file : str
            Path to temporary CDK App

        Returns
        -------
        Dict
            Stack Output values as dict
        """
        stack_file = self._create_temp_cdk_app()
        command = f"cdk deploy --app 'python {stack_file}' -O {self.stack_outputs_file}"

        # CDK launches a background task, so we must wait
        subprocess.check_output(command, shell=True)
        return self._read_stack_output()

    def _sync_stack_name(self, stack_output: Dict):
        """Synchronize initial stack name with CDK's final stack name

        Parameters
        ----------
        stack_output : Dict
            CDK CloudFormation Outputs, where the key is the stack name
        """
        self.stack_name = list(stack_output.keys())[0]

    def _read_stack_output(self):
        content = Path(self.stack_outputs_file).read_text()
        outputs: Dict = json.loads(content)

        self._sync_stack_name(stack_output=outputs)
        return dict(outputs.values())

    def _create_temp_cdk_app(self):
        """Autogenerate a CDK App with our Stack so that CDK CLI can deploy it

        This allows us to keep our BaseInfrastructure while supporting context lookups.
        """
        # tests/e2e/tracer
        stack_module_path = self.handlers_dir.relative_to(SOURCE_CODE_ROOT_PATH).parent

        # tests.e2e.tracer.infrastructure
        stack_infrastructure_module = str(stack_module_path / "infrastructure").replace(os.sep, ".")

        # TracerStack
        stack_infrastructure_name = self.__class__.__name__

        code = f"""
        from {stack_infrastructure_module} import {stack_infrastructure_name}
        stack = {stack_infrastructure_name}(handlers_dir="{self.handlers_dir}")
        stack.create_resources()
        stack.app.synth()
        """

        if not CDK_OUT_PATH.is_dir():
            CDK_OUT_PATH.mkdir()

        temp_file = CDK_OUT_PATH / f"{self.stack_name}_cdk_app.py"
        with temp_file.open("w") as fd:
            fd.write(textwrap.dedent(code))

        # allow CDK to read/execute file for stack deployment
        temp_file.chmod(0o755)
        return temp_file

    @abstractmethod
    def create_resources(self) -> None:
        """Create any necessary CDK resources. It'll be called before deploy

        Examples
        -------

        Creating a S3 bucket and export name and ARN

        ```python
        def created_resources(self):
            s3 = s3.Bucket(self.stack, "MyBucket")

            # This will create MyBucket and MyBucketArn CloudFormation Output
            self.add_cfn_output(name="MyBucket", value=s3.bucket_name, arn_value=bucket.bucket_arn)
        ```

        Creating Lambda functions available in the handlers directory

        ```python
        def created_resources(self):
            self.create_lambda_functions()
        ```
        """
        ...

    def add_cfn_output(self, name: str, value: str, arn: str = ""):
        """Create {Name} and optionally {Name}Arn CloudFormation Outputs.

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
        if arn:
            CfnOutput(self.stack, f"{name}Arn", value=arn)


def deploy_once(
    stack: Type[BaseInfrastructure],
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
    worker_id: str,
    layer_arn: str,
) -> Generator[Dict[str, str], None, None]:
    """Deploys provided stack once whether CPU parallelization is enabled or not

    Parameters
    ----------
    stack : Type[BaseInfrastructure]
        stack class to instantiate and deploy, for example MetricStack.
        Not to be confused with class instance (MetricStack()).
    request : pytest.FixtureRequest
        pytest request fixture to introspect absolute path to test being executed
    tmp_path_factory : pytest.TempPathFactory
        pytest temporary path factory to discover shared tmp when multiple CPU processes are spun up
    worker_id : str
        pytest-xdist worker identification to detect whether parallelization is enabled

    Yields
    ------
    Generator[Dict[str, str], None, None]
        stack CloudFormation outputs
    """
    handlers_dir = f"{request.node.path.parent}/handlers"
    stack = stack(handlers_dir=Path(handlers_dir), layer_arn=layer_arn)

    try:
        if worker_id == "master":
            # no parallelization, deploy stack and let fixture be cached
            yield stack.deploy()
        else:
            # tmp dir shared by all workers
            root_tmp_dir = tmp_path_factory.getbasetemp().parent
            cache = root_tmp_dir / f"{PYTHON_RUNTIME_VERSION}_cache.json"

            with FileLock(f"{cache}.lock"):
                # If cache exists, return stack outputs back
                # otherwise it's the first run by the main worker
                # deploy and return stack outputs so subsequent workers can reuse
                if cache.is_file():
                    stack_outputs = json.loads(cache.read_text())
                else:
                    stack_outputs: Dict = stack.deploy()
                    cache.write_text(json.dumps(stack_outputs))
            yield stack_outputs
    finally:
        stack.delete()


class LambdaLayerStack(BaseInfrastructure):
    FEATURE_NAME = "lambda-layer"

    def __init__(self, handlers_dir: Path, feature_name: str = FEATURE_NAME, layer_arn: str = "") -> None:
        super().__init__(feature_name, handlers_dir, layer_arn)

    def create_resources(self):
        layer = self._create_layer()
        CfnOutput(self.stack, "LayerArn", value=layer)

    def _create_layer(self) -> str:
        logger.debug("Creating Lambda Layer with latest source code available")
        output_dir = Path(str(AssetStaging.BUNDLING_OUTPUT_DIR), "python")
        input_dir = Path(str(AssetStaging.BUNDLING_INPUT_DIR), "aws_lambda_powertools")

        build_commands = [f"pip install .[pydantic] -t {output_dir}", f"cp -R {input_dir} {output_dir}"]
        layer = LayerVersion(
            self.stack,
            "aws-lambda-powertools-e2e-test",
            layer_version_name="aws-lambda-powertools-e2e-test",
            compatible_runtimes=[PythonVersion[PYTHON_RUNTIME_VERSION].value["runtime"]],
            code=Code.from_asset(
                path=str(SOURCE_CODE_ROOT_PATH),
                bundling=BundlingOptions(
                    image=DockerImage.from_build(
                        str(Path(__file__).parent),
                        build_args={"IMAGE": PythonVersion[PYTHON_RUNTIME_VERSION].value["image"]},
                    ),
                    command=["bash", "-c", " && ".join(build_commands)],
                ),
            ),
        )
        return layer.layer_version_arn


if __name__ == "__main__":
    layer = LambdaLayerStack(handlers_dir="")
    layer.create_resources()

    # Required for CDK CLI deploy
    layer.app.synth()
