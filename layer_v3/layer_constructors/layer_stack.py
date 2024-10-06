from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from aws_cdk import aws_lambda as lambda_

if TYPE_CHECKING:
    from constructs import Construct

from layer_v3.layer_constructors.helpers import construct_build_args


class LambdaPowertoolsLayerPythonV3(lambda_.LayerVersion):
    """
    A CDK Stack that creates a Lambda Layer for Powertools for AWS Lambda (Python) V3.

    This stack creates a Lambda Layer containing the Powertools for AWS Lambda (Python) V3 library.
    It allows customization of the Python runtime version, inclusion of extra dependencies,
    architecture, Powertools version, and layer name.

    Attributes:
        scope (Construct): The scope in which to define this construct.
        construct_id (str): The scoped construct ID. Must be unique amongst siblings in the same scope.
        python_version (lambda_.Runtime): The Python runtime version for the layer. Defaults to Python 3.12.
        include_extras (bool): Whether to include extra dependencies. Defaults to True.
        architecture (lambda_.Architecture): The compatible Lambda architecture. Defaults to x86_64.
        powertools_version (str): The version of Powertools to use. If empty, uses the latest version.
        layer_name (str): Custom name for the Lambda Layer. If empty, a default name will be used.

    Example:
        >>> app = cdk.App()
        >>> LambdaPowertoolsLayerPythonV3(app, "PowertoolsLayer",
        ...     python_version=lambda_.Runtime.PYTHON_3_11,
        ...     include_extras=False,
        ...     architecture=lambda_.Architecture.ARM_64,
        ...     powertools_version="2.10.0",
        ...     layer_name="MyCustomPowertoolsLayer")

    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        python_version: lambda_.Runtime = lambda_.Runtime.PYTHON_3_12,
        include_extras: bool = True,
        architecture: lambda_.Architecture = lambda_.Architecture.X86_64,
        powertools_version: str = "",
        layer_name: str = "",
    ) -> None:

        docker_file_path = str(Path(__file__).parent.parent / "docker")

        python_normalized_version: str = python_version.to_string().replace("python", "")

        if architecture.to_string() == "x86_64":
            docker_architecture: str = "linux/amd64"
        else:
            docker_architecture: str = "linux/arm64"

        super().__init__(
            scope,
            construct_id,
            code=lambda_.Code.from_docker_build(
                docker_file_path,
                build_args={
                    "PACKAGE_SUFFIX": construct_build_args(
                        include_extras,
                        powertools_version,
                    ),
                    "PYTHON_VERSION": python_normalized_version,
                },
                platform=docker_architecture,
            ),
            layer_version_name=layer_name,
            license="MIT-0",
            compatible_runtimes=[python_version],
            description=f"Powertools for AWS Lambda (Python) V3 [{architecture.to_string()} - Python {python_normalized_version}]"  # noqa E501
            + (" with extra dependencies" if include_extras else "")
            + (f" version {powertools_version}" if powertools_version else " latest version"),
            compatible_architectures=[architecture] if architecture else None,
        )
