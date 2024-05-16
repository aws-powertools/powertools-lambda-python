import pytest

from aws_lambda_powertools.utilities.data_classes import (
    CloudFormationCustomResourceEvent,
)
from aws_lambda_powertools.utilities.data_classes.cloudformation_custom_resource_event import (
    CloudFormationRequestType,
)
from tests.functional.utils import load_event


@pytest.mark.parametrize(
    "event_file",
    [
        "cloudformationCustomResourceCreate.json",
        "cloudformationCustomResourceUpdate.json",
        "cloudformationCustomResourceDelete.json",
    ],
)
def test_cloudformation_custom_resource_event(event_file):
    raw_event = load_event(event_file)
    parsed_event = CloudFormationCustomResourceEvent(raw_event)

    assert parsed_event.request_type == CloudFormationRequestType(raw_event["RequestType"])
    assert isinstance(parsed_event.request_type, CloudFormationRequestType)
    assert parsed_event.service_token == raw_event["ServiceToken"]
    assert parsed_event.stack_id == raw_event["StackId"]
    assert parsed_event.request_id == raw_event["RequestId"]
    assert parsed_event.logical_resource_id == raw_event["LogicalResourceId"]
    assert parsed_event.resource_type == raw_event["ResourceType"]
    assert parsed_event.resource_properties == raw_event.get("ResourceProperties")
    assert parsed_event.old_resource_properties == raw_event.get("OldResourceProperties")
