import json
import logging
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Callable, Dict, Generator, Optional
from uuid import uuid4

import boto3
import pytest
from aws_cdk import App, CfnOutput, Environment, RemovalPolicy, Stack, aws_logs
from aws_cdk.aws_lambda import (
    Architecture,
    Code,
    Function,
    LayerVersion,
    Runtime,
    Tracing,
)
from filelock import FileLock
from mypy_boto3_cloudformation import CloudFormationClient

from tests.e2e.utils.base import InfrastructureProvider
from tests.e2e.utils.constants import (
    CDK_OUT_PATH,
    PYTHON_RUNTIME_VERSION,
    SOURCE_CODE_ROOT_PATH,
)
from tests.e2e.utils.lambda_layer.powertools_layer import LocalLambdaPowertoolsLayer

logger = logging.getLogger(__name__)


class BaseInfrastructure(InfrastructureProvider):
    RANDOM_STACK_VALUE: str = f"{uuid4()}"

    def __init__(self) -> None:
        self.feature_path = Path(sys.modules[self.__class__.__module__].__file__).parent  # absolute path to feature
        self.feature_name = self.feature_path.parts[-1].replace("_", "-")  # logger, tracer, event-handler, etc.
        self.stack_name = f"test{PYTHON_RUNTIME_VERSION}-{self.feature_name}-{self.RANDOM_STACK_VALUE}"
        self.stack_outputs: Dict[str, str] = {}

        # NOTE: CDK stack account and region are tokens, we need to resolve earlier
        self.session = boto3.Session()
        self.cfn: CloudFormationClient = self.session.client("cloudformation")
        self.account_id = self.session.client("sts").get_caller_identity()["Account"]
        self.region = self.session.region_name

        self.app = App()
        self.stack = Stack(self.app, self.stack_name, env=Environment(account=self.account_id, region=self.region))

        # NOTE: Introspect feature details to generate CDK App (_create_temp_cdk_app method), Synth and Deployment
        self._feature_infra_class_name = self.__class__.__name__
        self._feature_infra_module_path = self.feature_path / "infrastructure"
        self._feature_infra_file = self.feature_path / "infrastructure.py"
        self._handlers_dir = self.feature_path / "handlers"
        self._cdk_out_dir: Path = CDK_OUT_PATH / self.feature_name
        self._stack_outputs_file = f'{self._cdk_out_dir / "stack_outputs.json"}'

        if not self._feature_infra_file.exists():
            raise FileNotFoundError(
                "You must have your infrastructure defined in 'tests/e2e/<feature>/infrastructure.py'.",
            )

    def create_lambda_functions(
        self,
        function_props: Optional[Dict] = None,
        architecture: Architecture = Architecture.X86_64,
    ) -> Dict[str, Function]:
        """Create Lambda functions available under handlers_dir

        It creates CloudFormation Outputs for every function found in PascalCase. For example,
        {handlers_dir}/basic_handler.py creates `BasicHandler` and `BasicHandlerArn` outputs.


        Parameters
        ----------
        function_props: Optional[Dict]
            Dictionary representing CDK Lambda FunctionProps to override defaults

        architecture: Architecture
            Used to create Lambda Layer and functions in a different architecture. Defaults to x86_64.

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

        Creating Lambda functions and override runtime to Python 3.10

        ```python
        from aws_cdk.aws_lambda import Runtime

        self.create_lambda_functions(function_props={"runtime": Runtime.PYTHON_3_10)
        ```
        """
        if not self._handlers_dir.exists():
            raise RuntimeError(f"Handlers dir '{self._handlers_dir}' must exist for functions to be created.")

        layer_build = LocalLambdaPowertoolsLayer(architecture=architecture).build()
        layer = LayerVersion(
            self.stack,
            "aws-lambda-powertools-e2e-test",
            layer_version_name="aws-lambda-powertools-e2e-test",
            compatible_runtimes=[
                Runtime.PYTHON_3_7,
                Runtime.PYTHON_3_8,
                Runtime.PYTHON_3_9,
                Runtime.PYTHON_3_10,
            ],
            compatible_architectures=[architecture],
            code=Code.from_asset(path=layer_build),
        )

        # NOTE: Agree on a convention if we need to support multi-file handlers
        # as we're simply taking any file under `handlers/` to be a Lambda function.
        handlers = list(self._handlers_dir.rglob("*.py"))
        source = Code.from_asset(f"{self._handlers_dir}")
        logger.debug(f"Creating functions for handlers: {handlers}")

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
                "runtime": self._determine_runtime_version(),
                "layers": [layer],
                "architecture": architecture,
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
        stack_file = self._create_temp_cdk_app()
        synth_command = f"npx cdk synth --app 'python {stack_file}' -o {self._cdk_out_dir}"
        deploy_command = (
            f"npx cdk deploy --app '{self._cdk_out_dir}' -O {self._stack_outputs_file} "
            "--require-approval=never --method=direct"
        )

        # CDK launches a background task, so we must wait
        subprocess.check_output(synth_command, shell=True)
        subprocess.check_output(deploy_command, shell=True)
        return self._read_stack_output()

    def delete(self) -> None:
        """Delete CloudFormation Stack"""
        logger.debug(f"Deleting stack: {self.stack_name}")
        self.cfn.delete_stack(StackName=self.stack_name)

    def _sync_stack_name(self, stack_output: Dict):
        """Synchronize initial stack name with CDK final stack name

        When using `cdk synth` with context methods (`from_lookup`),
        CDK can initialize the Stack multiple times until it resolves
        the context.

        Parameters
        ----------
        stack_output : Dict
            CDK CloudFormation Outputs, where the key is the stack name
        """
        self.stack_name = list(stack_output.keys())[0]

    def _read_stack_output(self):
        content = Path(self._stack_outputs_file).read_text()
        outputs: Dict = json.loads(content)
        self._sync_stack_name(stack_output=outputs)

        # discard stack_name and get outputs as dict
        self.stack_outputs = list(outputs.values())[0]
        return self.stack_outputs

    def _create_temp_cdk_app(self):
        """Autogenerate a CDK App with our Stack so that CDK CLI can deploy it

        This allows us to keep our BaseInfrastructure while supporting context lookups.
        """
        # cdk.out/tracer/cdk_app_v39.py
        temp_file = self._cdk_out_dir / f"cdk_app_{PYTHON_RUNTIME_VERSION}.py"

        if temp_file.exists():
            # no need to regenerate CDK app since it's just boilerplate
            return temp_file

        # Convert from POSIX path to Python module: tests.e2e.tracer.infrastructure
        infra_module = str(self._feature_infra_module_path.relative_to(SOURCE_CODE_ROOT_PATH)).replace(os.sep, ".")

        code = f"""
        from {infra_module} import {self._feature_infra_class_name}
        stack = {self._feature_infra_class_name}()
        stack.create_resources()
        stack.app.synth()
        """

        if not self._cdk_out_dir.is_dir():
            self._cdk_out_dir.mkdir(parents=True, exist_ok=True)

        with temp_file.open("w") as fd:
            fd.write(textwrap.dedent(code))

        # allow CDK to read/execute file for stack deployment
        temp_file.chmod(0o755)
        return temp_file

    def _determine_runtime_version(self) -> Runtime:
        """Determine Python runtime version based on the current Python interpreter"""
        version = sys.version_info
        if version.major == 3 and version.minor == 7:
            return Runtime.PYTHON_3_7
        elif version.major == 3 and version.minor == 8:
            return Runtime.PYTHON_3_8
        elif version.major == 3 and version.minor == 9:
            return Runtime.PYTHON_3_9
        elif version.major == 3 and version.minor == 10:
            return Runtime.PYTHON_3_10
        else:
            raise Exception(f"Unsupported Python version: {version}")

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
        raise NotImplementedError()

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


def call_once(
    task: Callable,
    tmp_path_factory: pytest.TempPathFactory,
    worker_id: str,
    callback: Optional[Callable] = None,
) -> Generator[object, None, None]:
    """Call function and serialize results once whether CPU parallelization is enabled or not

    Parameters
    ----------
    task : Callable
        Function to call once and JSON serialize result whether parallel test is enabled or not.
    tmp_path_factory : pytest.TempPathFactory
        pytest temporary path factory to discover shared tmp when multiple CPU processes are spun up
    worker_id : str
        pytest-xdist worker identification to detect whether parallelization is enabled
    callback : Callable
        Function to call when job is complete.

    Yields
    ------
    Generator[object, None, None]
        Callable output when called
    """

    try:
        if worker_id == "master":
            # no parallelization, call and return
            yield task()
        else:
            # tmp dir shared by all workers
            root_tmp_dir = tmp_path_factory.getbasetemp().parent
            cache = root_tmp_dir / f"{PYTHON_RUNTIME_VERSION}_cache.json"

            with FileLock(f"{cache}.lock"):
                # If cache exists, return task outputs back
                # otherwise it's the first run by the main worker
                # run and return task outputs for subsequent workers reuse
                if cache.is_file():
                    callable_result = json.loads(cache.read_text())
                else:
                    callable_result: Dict = task()
                    cache.write_text(json.dumps(callable_result))
            yield callable_result
    finally:
        if callback is not None:
            callback()
