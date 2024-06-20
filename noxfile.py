# Run nox tests
#
# usage:
#   poetry run nox --error-on-external-run --reuse-venv=yes --non-interactive
#
# If you want to target a specific Python version, add -p parameter

from typing import List, Optional

import nox

PREFIX_TESTS_FUNCTIONAL = "tests/functional"
PREFIX_TESTS_UNIT = "tests/unit"


def build_and_run_test(session: nox.Session, folders: List, extras: Optional[str] = "") -> None:
    """
    This function is responsible for setting up the testing environment and running the test suite for specific feature.

    The function performs the following tasks:
    1. Installs the required dependencies for executing any test
    2. If the `extras` parameter is provided, the function installs the additional dependencies
    3. the function runs the pytest command with the specified folders as arguments, executing the test suite.

    Parameters
    ----------
    session: nox.Session
        The current Nox session object, which is used to manage the virtual environment and execute commands.
    folders: List
        A list of folder paths that contain the test files to be executed.
    extras: Optional[str]
        A string representing additional dependencies that should be installed for the test environment.
        If not provided, the function will install the project with basic dependencies
    """

    # Required install to execute any test
    session.install("poetry", "pytest", "pytest-mock", "pytest_socket")

    # Powertools project folder is in the root
    if extras:
        session.install(f"./[{extras}]")
    else:
        session.install("./")

    # Execute test in specific folders
    session.run("pytest", *folders)


@nox.session()
def test_with_only_required_packages(session: nox.Session):
    """Tests that only depends for required libraries"""
    # Logger
    # Metrics - Amazon CloudWatch EMF
    # Metrics - Base provider
    # Middleware factory without tracer
    # Typing
    # Data Class - without codepipeline dataclass
    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/logger/required_dependencies/",
            f"{PREFIX_TESTS_FUNCTIONAL}/metrics/required_dependencies/",
            f"{PREFIX_TESTS_FUNCTIONAL}/middleware_factory/required_dependencies/",
            f"{PREFIX_TESTS_FUNCTIONAL}/typing/required_dependencies/",
            f"{PREFIX_TESTS_UNIT}/data_classes/required_dependencies/",
        ],
    )


@nox.session()
def test_with_datadog_as_required_package(session: nox.Session):
    """Tests that depends on Datadog library"""
    # Metrics - Datadog
    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/metrics/datadog/",
        ],
        extras="datadog",
    )


@nox.session()
def test_with_xray_sdk_as_required_package(session: nox.Session):
    """Tests that depends on AWS XRAY SDK library"""
    # Tracer
    # Middleware factory with tracer
    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/tracer/_aws_xray_sdk/",
            f"{PREFIX_TESTS_FUNCTIONAL}/middleware_factory/_aws_xray_sdk/",
        ],
        extras="tracer",
    )


@nox.session()
def test_with_boto3_sdk_as_required_package(session: nox.Session):
    """Tests that depends on boto3/botocore library"""
    # Parameters
    # Feature Flags
    # Data Class - only codepipeline dataclass
    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/parameters/_boto3/",
            f"{PREFIX_TESTS_FUNCTIONAL}/feature_flags/_boto3/",
            f"{PREFIX_TESTS_UNIT}/data_classes/_boto3/",
        ],
        extras="aws-sdk",
    )


@nox.session()
def test_with_fastjsonschema_as_required_package(session: nox.Session):
    """Tests that depends on boto3/botocore library"""
    # Validation
    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/validator/_fastjsonschema/",
        ],
        extras="validation",
    )


@nox.session()
def test_with_aws_encryption_sdk_as_required_package(session: nox.Session):
    """Tests that depends on aws_encryption_sdk library"""
    # Data Masking
    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/data_masking/_aws_encryption_sdk/",
            f"{PREFIX_TESTS_UNIT}/data_masking/_aws_encryption_sdk/",
        ],
        extras="datamasking",
    )
