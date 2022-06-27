import datetime
import sys
import uuid
from dataclasses import dataclass

import boto3

# We only need typing_extensions for python versions <3.8
if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from typing import Dict, Generator, Optional

import pytest
from e2e.utils import helpers, infrastructure


class LambdaConfig(TypedDict):
    parameters: dict
    environment_variables: Dict[str, str]


@dataclass
class InfrastructureOutput:
    arns: Dict[str, str]
    execution_time: datetime.datetime

    def get_lambda_arns(self) -> Dict[str, str]:
        return self.arns

    def get_lambda_arn(self, name: str) -> Optional[str]:
        return self.arns.get(name)

    def get_lambda_execution_time(self) -> datetime.datetime:
        return self.execution_time

    def get_lambda_execution_time_timestamp(self) -> int:
        return int(self.execution_time.timestamp() * 1000)


@pytest.fixture(scope="module")
def create_infrastructure(config, request) -> Generator[Dict[str, str], None, None]:
    stack_name = f"test-lambda-{uuid.uuid4()}"
    test_dir = request.fspath.dirname
    handlers_dir = f"{test_dir}/handlers/"

    infra = infrastructure.Infrastructure(stack_name=stack_name, handlers_dir=handlers_dir, config=config)
    yield infra.deploy(Stack=infrastructure.InfrastructureStack)
    infra.delete()


@pytest.fixture(scope="module")
def execute_lambda(create_infrastructure) -> InfrastructureOutput:
    execution_time = datetime.datetime.utcnow()
    session = boto3.Session()
    client = session.client("lambda")
    for _, arn in create_infrastructure.items():
        helpers.trigger_lambda(lambda_arn=arn, client=client)
    return InfrastructureOutput(arns=create_infrastructure, execution_time=execution_time)
