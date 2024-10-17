import aws_cdk
import pytest
from aws_cdk import assertions
from aws_cdk import aws_lambda as lambda_

from layer_v3.layer_constructors.helpers import construct_build_args
from layer_v3.layer_constructors.layer_stack import LambdaPowertoolsLayerPythonV3


def test_with_no_configuration_constructor():

    app = aws_cdk.App()
    stack = aws_cdk.Stack(app, "TestStack")
    LambdaPowertoolsLayerPythonV3(stack, "LambdaPowertoolsLayerPythonV3")

    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::Lambda::LayerVersion", {"LicenseInfo": "MIT-0"})

    template.has_resource_properties("AWS::Lambda::LayerVersion", {"CompatibleRuntimes": ["python3.12"]})


@pytest.mark.parametrize(
    "python_version",
    [
        lambda_.Runtime.PYTHON_3_8,
        lambda_.Runtime.PYTHON_3_9,
        lambda_.Runtime.PYTHON_3_10,
        lambda_.Runtime.PYTHON_3_11,
        lambda_.Runtime.PYTHON_3_12,
    ],
)
def test_with_different_python_version_x86_64(python_version):

    inner_python_version: lambda_.Runtime = python_version

    app = aws_cdk.App()
    stack = aws_cdk.Stack(app, "TestStack")

    LambdaPowertoolsLayerPythonV3(
        stack,
        "LambdaPowertoolsLayerPythonV3",
        python_version=inner_python_version,
        powertools_version="3.0.0",
        layer_name="Powertools",
    )
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::Lambda::LayerVersion", {"LicenseInfo": "MIT-0"})

    template.has_resource_properties(
        "AWS::Lambda::LayerVersion",
        {"CompatibleRuntimes": [inner_python_version.to_string()]},
    )

    template.has_resource_properties("AWS::Lambda::LayerVersion", {"CompatibleArchitectures": ["x86_64"]})


@pytest.mark.parametrize(
    "python_version",
    [
        lambda_.Runtime.PYTHON_3_8,
        lambda_.Runtime.PYTHON_3_9,
        lambda_.Runtime.PYTHON_3_10,
        lambda_.Runtime.PYTHON_3_11,
        lambda_.Runtime.PYTHON_3_12,
    ],
)
def test_with_different_python_version_arm64(python_version):

    inner_python_version: lambda_.Runtime = python_version

    app = aws_cdk.App()
    stack = aws_cdk.Stack(app, "TestStack")
    LambdaPowertoolsLayerPythonV3(
        stack,
        "LambdaPowertoolsLayerPythonV3",
        python_version=inner_python_version,
        architecture=lambda_.Architecture.ARM_64,
        powertools_version="3.0.0",
        layer_name="Powertools",
    )
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::Lambda::LayerVersion", {"LicenseInfo": "MIT-0"})

    template.has_resource_properties(
        "AWS::Lambda::LayerVersion",
        {"CompatibleRuntimes": [inner_python_version.to_string()]},
    )

    template.has_resource_properties("AWS::Lambda::LayerVersion", {"CompatibleArchitectures": ["arm64"]})


def test_with_custom_name():

    app = aws_cdk.App()
    stack = aws_cdk.Stack(app, "TestStack")
    LambdaPowertoolsLayerPythonV3(stack, "LambdaPowertoolsLayerPythonV3", layer_name="custom_name_layer")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::Lambda::LayerVersion", {"LayerName": "custom_name_layer"})

    template.has_resource_properties(
        "AWS::Lambda::LayerVersion",
        {
            "Description": "Powertools for AWS Lambda (Python) V3 [x86_64 - Python 3.12] with extra dependencies latest version",  # noqa E501
        },
    )


def test_with_extras():

    app = aws_cdk.App()
    stack = aws_cdk.Stack(app, "TestStack")
    LambdaPowertoolsLayerPythonV3(
        stack,
        "LambdaPowertoolsLayerPythonV3",
        layer_name="custom_name_layer",
        include_extras=True,
        powertools_version="3.0.0",
    )
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::Lambda::LayerVersion", {"LayerName": "custom_name_layer"})

    template.has_resource_properties(
        "AWS::Lambda::LayerVersion",
        {
            "Description": "Powertools for AWS Lambda (Python) V3 [x86_64 - Python 3.12] with extra dependencies version 3.0.0",  # noqa E501
        },
    )


def test_with_extras_arm64():

    app = aws_cdk.App()
    stack = aws_cdk.Stack(app, "TestStack")
    LambdaPowertoolsLayerPythonV3(
        stack,
        "LambdaPowertoolsLayerPythonV3",
        layer_name="custom_name_layer",
        include_extras=True,
        powertools_version="3.0.0",
        architecture=lambda_.Architecture.ARM_64,
    )
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::Lambda::LayerVersion", {"LayerName": "custom_name_layer"})

    template.has_resource_properties(
        "AWS::Lambda::LayerVersion",
        {
            "Description": "Powertools for AWS Lambda (Python) V3 [arm64 - Python 3.12] with extra dependencies version 3.0.0",  # noqa E501
        },
    )


def test_build_args_with_version():

    build_args = construct_build_args(include_extras=True, version="3.0.0")

    assert build_args == "[all]==3.0.0"


def test_build_args_without_version():

    build_args = construct_build_args(include_extras=True)

    assert build_args == "[all]"


def test_build_args_with_github_tag():

    version = "git+https://github.com/awslabs/aws-lambda-powertools-python@v2"

    build_args = construct_build_args(include_extras=True, version=version)

    assert build_args == f"[all] @ {version}"


def test_build_args_with_no_version_and_no_extra():

    build_args = construct_build_args(include_extras=False)

    assert build_args == ""
