import pytest
from pydantic import BaseModel, Field

from aws_lambda_powertools.utilities.parser import ValidationError, event_parser
from aws_lambda_powertools.utilities.parser.models import (
    CloudFormationCustomResourceCreateModel,
    CloudFormationCustomResourceDeleteModel,
    CloudFormationCustomResourceUpdateModel,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.utils import load_event


@event_parser(model=CloudFormationCustomResourceUpdateModel)
def handle_update_custom_resource(event: CloudFormationCustomResourceUpdateModel, _: LambdaContext):
    assert event.request_type == "Update"
    assert event.request_id == "xxxxx-d2a0-4dfb-ab1f-xxxxxx"
    assert event.service_token == "arn:aws:lambda:us-east-1:xxx:function:xxxx-CrbuiltinfunctionidProvi-2vKAalSppmKe"
    assert (
        str(event.response_url)
        == "https://cloudformation-custom-resource-response-useast1.s3.amazonaws.com/7F%7Cb1f50fdfc25f3b"
    )
    assert event.stack_id == "arn:aws:cloudformation:us-east-1:xxxx:stack/xxxx/271845b0-f2e8-11ed-90ac-0eeb25b8ae21"
    assert event.logical_resource_id == "xxxxxxxxx"
    assert event.resource_type == "Custom::MyType"
    assert event.resource_properties == {
        "ServiceToken": "arn:aws:lambda:us-east-1:xxxxx:function:xxxxx",
        "MyProps": "new",
    }
    assert event.old_resource_properties == {
        "ServiceToken": "arn:aws:lambda:us-east-1:xxxxx:function:xxxxx-xxxx-xxx",
        "MyProps": "old",
    }


def test_update_trigger_event():
    event_dict = load_event("cloudformationCustomResourceUpdate.json")
    handle_update_custom_resource(event_dict, LambdaContext())


def test_validate_update_event_does_not_conform_with_model():
    event = {"invalid": "event"}
    with pytest.raises(ValidationError):
        handle_update_custom_resource(event, LambdaContext())


# NOTE: Leftover, move to create model test
class MyModel(BaseModel):
    MyProps: str


# NOTE: Leftover, update to test only custom model per se
def test_cloudformation_custom_resource_create_event_custom_model():
    class MyCustomResource(CloudFormationCustomResourceCreateModel):
        resource_properties: MyModel = Field(..., alias="ResourceProperties")

    raw_event = load_event("cloudformationCustomResourceCreate.json")
    model = MyCustomResource(**raw_event)

    assert model.request_type == raw_event["RequestType"]
    assert model.request_id == raw_event["RequestId"]
    assert model.service_token == raw_event["ServiceToken"]
    assert str(model.response_url) == raw_event["ResponseURL"]
    assert model.stack_id == raw_event["StackId"]
    assert model.logical_resource_id == raw_event["LogicalResourceId"]
    assert model.resource_type == raw_event["ResourceType"]
    assert model.resource_properties.MyProps == raw_event["ResourceProperties"].get("MyProps")


def test_cloudformation_custom_resource_create_event():
    raw_event = load_event("cloudformationCustomResourceCreate.json")
    model = CloudFormationCustomResourceCreateModel(**raw_event)

    assert model.request_type == raw_event["RequestType"]
    assert model.request_id == raw_event["RequestId"]
    assert model.service_token == raw_event["ServiceToken"]
    assert str(model.response_url) == raw_event["ResponseURL"]
    assert model.stack_id == raw_event["StackId"]
    assert model.logical_resource_id == raw_event["LogicalResourceId"]
    assert model.resource_type == raw_event["ResourceType"]
    assert model.resource_properties == raw_event["ResourceProperties"]


def test_cloudformation_custom_resource_create_event_invalid():
    raw_event = load_event("cloudformationCustomResourceCreate.json")
    raw_event["ResourceProperties"] = ["some_data"]

    with pytest.raises(ValidationError):
        CloudFormationCustomResourceCreateModel(**raw_event)


def test_cloudformation_custom_resource_delete_event():
    raw_event = load_event("cloudformationCustomResourceDelete.json")
    model = CloudFormationCustomResourceDeleteModel(**raw_event)

    assert model.request_type == raw_event["RequestType"]
    assert model.request_id == raw_event["RequestId"]
    assert model.service_token == raw_event["ServiceToken"]
    assert str(model.response_url) == raw_event["ResponseURL"]
    assert model.stack_id == raw_event["StackId"]
    assert model.logical_resource_id == raw_event["LogicalResourceId"]
    assert model.resource_type == raw_event["ResourceType"]
    assert model.resource_properties == raw_event["ResourceProperties"]


def test_cloudformation_custom_resource_delete_event_invalid():
    raw_event = load_event("cloudformationCustomResourceDelete.json")
    raw_event["ResourceProperties"] = ["some_data"]
    with pytest.raises(ValidationError):
        CloudFormationCustomResourceDeleteModel(**raw_event)
