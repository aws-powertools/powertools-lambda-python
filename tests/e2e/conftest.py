import uuid

import boto3
import pytest
import yaml
from aws_cdk import App, CfnOutput, RemovalPolicy, Stack, aws_lambda_python_alpha, aws_logs
from aws_cdk.aws_lambda import Code, Function, Runtime, Tracing

from . import utils


def transform_output(outputs):
    return {output["OutputKey"]: output["OutputValue"] for output in outputs if output["OutputKey"]}


# Create CDK cloud assembly code
def prepare_infrastructure(handlers_name, handlers_dir, stack_name, environment_variables, **config):
    integration_test_app = App()
    stack = Stack(integration_test_app, stack_name)
    powertools_layer = aws_lambda_python_alpha.PythonLayerVersion(
        stack,
        "aws-lambda-powertools",
        layer_version_name="aws-lambda-powertools",
        entry=".",
        compatible_runtimes=[Runtime.PYTHON_3_9],
    )
    code = Code.from_asset(handlers_dir)

    for filename in handlers_name:

        function_python = Function(
            stack,
            f"{filename}-lambda",
            runtime=Runtime.PYTHON_3_9,
            code=code,
            handler=f"{filename}.lambda_handler",
            layers=[powertools_layer],
            environment=environment_variables,
            tracing=Tracing.ACTIVE if config.get("tracing") == "ACTIVE" else Tracing.DISABLED,
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
        integration_test_app.synth().get_stack_by_name(stack_name).template,
        integration_test_app.synth().directory,
        integration_test_app.synth().artifacts,
    )


def deploy_infrastructure(template, asset_root_dir, stack_name, client):

    utils.upload_assets(template, asset_root_dir)

    response = client.create_stack(
        StackName=stack_name,
        TemplateBody=yaml.dump(template),
        TimeoutInMinutes=10,
        OnFailure="DO_NOTHING",
        Capabilities=["CAPABILITY_IAM"],
    )
    waiter = client.get_waiter("stack_create_complete")
    waiter.wait(StackName=stack_name, WaiterConfig={"Delay": 2, "MaxAttempts": 50})
    response = client.describe_stacks(StackName=stack_name)
    return response["Stacks"][0]["Outputs"]


@pytest.fixture(scope="session")
def deploy():
    cf_client = boto3.Session().client("cloudformation")
    stack_name = f"test-lambda-{uuid.uuid4()}"

    def deploy(handlers_name, handlers_dir, environment_variables, **config):

        template, asset_root_dir, artifact = prepare_infrastructure(
            handlers_name=handlers_name,
            handlers_dir=handlers_dir,
            stack_name=stack_name,
            environment_variables=environment_variables,
            **config,
        )
        outputs = deploy_infrastructure(
            template=template, asset_root_dir=asset_root_dir, stack_name=stack_name, client=cf_client
        )
        return transform_output(outputs)

    yield deploy
    # Ensure stack deletion is triggered at the end of the test session
    cf_client.delete_stack(StackName=stack_name)
