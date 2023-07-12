import json
from typing import Any, Dict, List

import pytest

from tests.e2e.utils import data_fetcher


@pytest.fixture
def ssm_get_parameters_by_name_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("ParameterSsmGetParametersByNameArn", "")


@pytest.fixture
def parameters_list(infrastructure: dict) -> List[str]:
    param_list = infrastructure.get("ParametersNameList", "[]")
    return json.loads(param_list)


@pytest.mark.xdist_group(name="parameters")
def test_get_parameters_by_name(
    ssm_get_parameters_by_name_fn_arn: str,
    parameters_list: str,
):
    # GIVEN/WHEN
    function_response, _ = data_fetcher.get_lambda_response(lambda_arn=ssm_get_parameters_by_name_fn_arn)
    parameter_values: Dict[str, Any] = json.loads(function_response["Payload"].read().decode("utf-8"))

    # THEN
    for param in parameters_list:
        try:
            assert parameter_values[param] is not None
        except (KeyError, TypeError):
            pytest.fail(f"Parameter {param} not found in response")
