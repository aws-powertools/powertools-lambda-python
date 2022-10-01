import json

import pytest

from tests.e2e.utils import data_fetcher


@pytest.fixture
def parameter_string_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("ParameterStringHandlerArn", "")


@pytest.fixture
def parameter_appconfig_freeform_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("ParameterAppconfigFreeformHandlerArn", "")


@pytest.fixture
def parameter_appconfig_freeform_handler_fn(infrastructure: dict) -> str:
    return infrastructure.get("ParameterAppconfigFreeformHandler", "")


@pytest.fixture
def secret_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("SecretHandlerArn", "")


@pytest.fixture
def parameter_name(infrastructure: dict) -> str:
    return infrastructure.get("ParameterString", "")


def test_simple_parameter_string(parameter_string_handler_fn_arn: str):
    # GIVEN
    expected_return = json.dumps({"value": "Lambda Powertools"})

    # WHEN
    parameter_execution, _ = data_fetcher.get_lambda_response(lambda_arn=parameter_string_handler_fn_arn)
    parameter_value = parameter_execution["Payload"].read().decode("utf-8")

    # THEN
    assert parameter_value == expected_return


def test_get_parameter_appconfig_freeform(
    parameter_appconfig_freeform_handler_fn_arn: str, parameter_appconfig_freeform_handler_fn: str
):
    # GIVEN
    payload = json.dumps({"name": "profilee2e", "environment": "enve2e", "application": "appe2e"})
    expected_return = json.dumps({"save_history": {"default": True}})

    # WHEN
    parameter_execution, _ = data_fetcher.get_lambda_response(
        lambda_arn=parameter_appconfig_freeform_handler_fn_arn, payload=payload
    )
    parameter_value = parameter_execution["Payload"].read().decode("utf-8")

    assert parameter_value == expected_return
