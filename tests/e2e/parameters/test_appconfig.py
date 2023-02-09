import json

import pytest

from tests.e2e.utils import data_fetcher


@pytest.fixture
def parameter_appconfig_freeform_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("ParameterAppconfigFreeformHandlerArn", "")


@pytest.fixture
def parameter_appconfig_freeform_handler_fn(infrastructure: dict) -> str:
    return infrastructure.get("ParameterAppconfigFreeformHandler", "")


@pytest.fixture
def parameter_appconfig_freeform_value(infrastructure: dict) -> str:
    return infrastructure.get("AppConfigConfigurationValue", "")


@pytest.fixture
def parameter_appconfig_freeform_application(infrastructure: dict) -> str:
    return infrastructure.get("AppConfigApplication", "")


@pytest.fixture
def parameter_appconfig_freeform_environment(infrastructure: dict) -> str:
    return infrastructure.get("AppConfigEnvironment", "")


@pytest.fixture
def parameter_appconfig_freeform_profile(infrastructure: dict) -> str:
    return infrastructure.get("AppConfigProfile", "")


@pytest.mark.xdist_group(name="parameters")
def test_get_parameter_appconfig_freeform(
    parameter_appconfig_freeform_handler_fn_arn: str,
    parameter_appconfig_freeform_value: str,
    parameter_appconfig_freeform_application: str,
    parameter_appconfig_freeform_environment: str,
    parameter_appconfig_freeform_profile: str,
):
    # GIVEN
    payload = json.dumps(
        {
            "name": parameter_appconfig_freeform_profile,
            "environment": parameter_appconfig_freeform_environment,
            "application": parameter_appconfig_freeform_application,
        }
    )
    expected_return = parameter_appconfig_freeform_value

    # WHEN
    parameter_execution, _ = data_fetcher.get_lambda_response(
        lambda_arn=parameter_appconfig_freeform_handler_fn_arn, payload=payload
    )
    parameter_value = parameter_execution["Payload"].read().decode("utf-8")

    assert parameter_value == expected_return
