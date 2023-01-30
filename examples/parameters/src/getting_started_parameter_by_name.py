from typing import Any

from aws_lambda_powertools.utilities.parameters.ssm import get_parameters_by_name

parameters = {
    "/develop/service/commons/telemetry/config": {"max_age": 300, "transform": "json"},
    "/no_cache_param": {"max_age": 0},
    # inherit default values
    "/develop/service/payment/api/capture/url": {},
}


def handler(event, context):
    # This returns a dict with the parameter name as key
    response: dict[str, Any] = get_parameters_by_name(parameters=parameters, max_age=60)
    for parameter, value in response.items():
        print(f"{parameter}: {value}")
