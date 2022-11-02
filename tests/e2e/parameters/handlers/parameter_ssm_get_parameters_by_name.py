import json
import os
from typing import Any, Dict, List, cast

from aws_lambda_powertools.utilities.parameters.ssm import get_parameters_by_name
from aws_lambda_powertools.utilities.typing import LambdaContext

parameters_list: List[str] = cast(List, json.loads(os.getenv("parameters", "")))


def lambda_handler(event: dict, context: LambdaContext) -> Dict[str, Any]:
    parameters_to_fetch: Dict[str, Any] = {param: {} for param in parameters_list}

    # response`{parameter:value}`
    return get_parameters_by_name(parameters=parameters_to_fetch, max_age=0)
