import pytest

from aws_lambda_powertools.utilities.data_classes import (
    CodeDeployLifeCycleHookLambdaEvent,
)
from tests.functional.utils import load_event


@pytest.mark.parametrize(
    "event_file",
    [
        "codeDeployLifecycleHookEvent.json",
    ],
)
def test_code_deploy_lifecycle_hook_event(event_file):
    raw_event = load_event(event_file)
    parsed_event = CodeDeployLifeCycleHookLambdaEvent(raw_event)

    assert parsed_event.deployment_id == raw_event["DeploymentId"]
    assert parsed_event.lifecycle_event_hook_execution_id == raw_event["LifecycleEventHookExecutionId"]
