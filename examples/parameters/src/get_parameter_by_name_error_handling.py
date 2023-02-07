from typing import Any

from aws_lambda_powertools.utilities.parameters.ssm import get_parameters_by_name

parameters = {
    "/develop/service/commons/telemetry/config": {"max_age": 300, "transform": "json"},
    # it would fail by default
    "/this/param/does/not/exist": {},
}


def handler(event, context):
    values: dict[str, Any] = get_parameters_by_name(parameters=parameters, raise_on_error=False)
    errors: list[str] = values.get("_errors", [])

    # Handle gracefully, since '/this/param/does/not/exist' will only be available in `_errors`
    if errors:
        ...

    for parameter, value in values.items():
        print(f"{parameter}: {value}")
