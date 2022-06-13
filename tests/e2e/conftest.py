import datetime
import sys
import uuid

# We only need typing_extensions for python versions <3.8
if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from typing import Dict, Generator

import pytest
from e2e.utils import helpers, infrastructure


class LambdaConfig(TypedDict):
    parameters: dict
    environment_variables: Dict[str, str]


class LambdaExecution(TypedDict):
    arns: Dict[str, str]
    execution_time: datetime.datetime


@pytest.fixture(scope="module")
def execute_lambda(config, request) -> Generator[LambdaExecution, None, None]:
    stack_name = f"test-lambda-{uuid.uuid4()}"
    test_dir = request.fspath.dirname
    handlers_dir = f"{test_dir}/handlers/"

    infra = infrastructure.Infrastructure(
        stack_name=stack_name,
        handlers_dir=handlers_dir,
        config=config["parameters"],
        environment_variables=config["environment_variables"],
    )

    lambda_arns = infra.deploy()
    execution_time = datetime.datetime.utcnow()

    for name, arn in lambda_arns.items():
        helpers.trigger_lambda(lambda_arn=arn, client=infra.lambda_client)
    yield {"arns": lambda_arns, "execution_time": execution_time}
    # Ensure stack deletion is triggered at the end of the test session
    infra.delete()
