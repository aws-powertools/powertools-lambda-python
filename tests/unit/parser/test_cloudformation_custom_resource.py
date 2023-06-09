import pytest
from pydantic import BaseModel, Field

from aws_lambda_powertools.utilities.parser import ValidationError
from aws_lambda_powertools.utilities.parser.models import (
    CloudFormationCustomResourceCreateModel,
    CloudFormationCustomResourceDeleteModel,
    CloudFormationCustomResourceUpdateModel,
)
from tests.functional.utils import load_event


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


def test_cloudformation_custom_resource_create_event_custom_model():
    class MyModel(BaseModel):
        MyProps: str

    class MyCustomResource(CloudFormationCustomResourceCreateModel):
        resource_properties: MyModel = Field(..., alias="ResourceProperties")

    raw_event = load_event("cloudformationCustomResourceCreate.json")
    model = MyCustomResource(**raw_event)

    assert model.resource_properties.MyProps == raw_event["ResourceProperties"].get("MyProps")


def test_cloudformation_custom_resource_create_event_invalid():
    raw_event = load_event("cloudformationCustomResourceCreate.json")
    raw_event["ResourceProperties"] = ["some_data"]

    with pytest.raises(ValidationError):
        CloudFormationCustomResourceCreateModel(**raw_event)


def test_cloudformation_custom_resource_update_event():
    raw_event = load_event("cloudformationCustomResourceUpdate.json")
    model = CloudFormationCustomResourceUpdateModel(**raw_event)

    assert model.request_type == raw_event["RequestType"]
    assert model.request_id == raw_event["RequestId"]
    assert model.service_token == raw_event["ServiceToken"]
    assert str(model.response_url) == raw_event["ResponseURL"]
    assert model.stack_id == raw_event["StackId"]
    assert model.logical_resource_id == raw_event["LogicalResourceId"]
    assert model.resource_type == raw_event["ResourceType"]
    assert model.resource_properties == raw_event["ResourceProperties"]
    assert model.old_resource_properties == raw_event["OldResourceProperties"]


def test_cloudformation_custom_resource_update_event_invalid():
    raw_event = load_event("cloudformationCustomResourceUpdate.json")
    raw_event["OldResourceProperties"] = ["some_data"]

    with pytest.raises(ValidationError):
        CloudFormationCustomResourceUpdateModel(**raw_event)


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
