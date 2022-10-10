import pytest

from tests.e2e.utils import data_fetcher


@pytest.fixture
def parameter_string_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("ParameterStringHandlerArn", "")


@pytest.fixture
def parameter_string_value(infrastructure: dict) -> str:
    return infrastructure.get("ParameterStringValue", "")


def test_simple_parameter_string(parameter_string_handler_fn_arn: str, parameter_string_value: str):
    # GIVEN
    expected_return = parameter_string_value

    # WHEN
    parameter_execution, _ = data_fetcher.get_lambda_response(lambda_arn=parameter_string_handler_fn_arn)
    parameter_value = parameter_execution["Payload"].read().decode("utf-8")

    # THEN
    assert parameter_value == expected_return
