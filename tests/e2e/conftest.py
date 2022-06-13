import datetime
import uuid
from typing import Generator, TypedDict

import pytest
from e2e.utils import helpers, infrastructure


class LambdaConfig(TypedDict):
    parameters: dict
    environment_variables: dict[str, str]


class LambdaExecution(TypedDict):
    arns: dict[str, str]
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
