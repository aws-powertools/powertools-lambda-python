import subprocess
import tempfile
import uuid
from pathlib import Path

import boto3
import pytest
from aws_cdk import App, BundlingOptions, CfnOutput, DockerVolume, Stack, aws_lambda_python_alpha, aws_logs
from aws_cdk.aws_lambda import Code, Function, LayerVersion, Runtime, Tracing


def get_data(outputs, key):
    value = None
    for output in outputs:
        if output["OutputKey"] == key:
            value = output["OutputValue"]
    return value


def load_handler_file(tmp_filename, handler_filename):

    with open(tmp_filename, mode="wb+") as tmp:
        with open(handler_filename, mode="rb") as handler:
            for line in handler:
                tmp.write(line)
    return tmp


# Create CDK cloud assembly code
def cdk_infrastructure(handler_file, stack_name, environment_variables, **config):
    integration_test_app = App()
    stack = Stack(integration_test_app, stack_name)
    powertools_layer = LayerVersion.from_layer_version_arn(
        stack,
        "aws-lambda-powertools",
        "arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPython:15",
    )
    # TODO Create only one layer per test suite as it takes 4 additional minutes to deploy stack without cache
    # TODO layer creation breaks hot-swap deployment as CDK complains that change contains non-Asset changes.
    # powertools_layer = aws_lambda_python_alpha.PythonLayerVersion(
    #     stack,
    #     "aws-lambda-powertools",
    #     layer_version_name="aws-lambda-powertools",
    #     entry=".",
    #     compatible_runtimes=runtimes,
    # )
    code = Code.from_asset(str(Path(handler_file).parent))
    # powertools_root_dir = "."
    # tmp_handler_dir = str(Path(handler_file).parent)
    # code = Code.from_asset(
    #     path=powertools_root_dir,
    #     bundling=BundlingOptions(
    #         image=Runtime.PYTHON_3_9.bundling_image,
    #         volumes=[DockerVolume(container_path=tmp_handler_dir, host_path=tmp_handler_dir)],
    #         user="root",
    #         command=[
    #             "bash",
    #             "-c",
    #             f"pip install poetry && poetry export -f requirements.txt --without-hashes > requirements.txt && pip install -r requirements.txt -t /asset-output/ && rsync -r aws_lambda_powertools /asset-output/ && rsync -r {tmp_handler_dir}/ /asset-output",
    #         ],
    #     ),
    # )

    function_python = Function(
        stack,
        "MyFunction",
        runtime=Runtime.PYTHON_3_9,
        code=code,
        handler=f"{Path(handler_file).stem}.lambda_handler",
        layers=[powertools_layer],
        log_retention=aws_logs.RetentionDays.ONE_DAY,
        environment=environment_variables,
        tracing=Tracing.ACTIVE if config.get("tracing") == "ACTIVE" else Tracing.DISABLED,
    )

    CfnOutput(stack, "lambdaArn", value=function_python.function_arn)
    integration_test_app.synth()
    return integration_test_app


# Deploy synthesized code using CDK CLI
def deploy_app(path, stack_name, cf_client):
    result = subprocess.run(
        [
            "cdk",
            "deploy",
            "--app",
            str(path),
            "--require-approval",
            "never",
            "--hotswap",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    print(result.returncode, result.stdout, result.stderr)

    outputs = cf_client.describe_stacks(StackName=stack_name)["Stacks"][0]["Outputs"]
    return outputs


@pytest.fixture(scope="session")
def deploy_infrastructure():
    cf_client = boto3.Session().client("cloudformation")
    # in order to use hotswap we create tmp file that we specify as cdk lambda asset
    # and we dynamically change its content
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_filename = f"{tmp_dir}/tmp.py"
        stack_name = f"test-lambda-{uuid.uuid4()}"

        def deploy(handler_filename, environment_variables, **config):
            load_handler_file(tmp_filename=tmp_filename, handler_filename=handler_filename)
            app = cdk_infrastructure(
                handler_file=tmp_filename, stack_name=stack_name, environment_variables=environment_variables, **config
            )

            outputs = deploy_app(path=app.outdir, stack_name=stack_name, cf_client=cf_client)
            lambda_arn = get_data(outputs=outputs, key="lambdaArn")
            return lambda_arn

        yield deploy
        # Ensure stack deletion is triggered at the end of the test session
        cf_client.delete_stack(StackName=stack_name)
