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


@event_parser(model=CloudFormationCustomResourceCreateModel)
def handle_create_custom_resource(event: CloudFormationCustomResourceCreateModel, _: LambdaContext):
    assert event.request_type == "Create"
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
        "MyProps": "ss",
    }


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


@event_parser(model=CloudFormationCustomResourceDeleteModel)
def handle_delete_custom_resource(event: CloudFormationCustomResourceDeleteModel, _: LambdaContext):
    assert event.request_type == "Delete"
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
        "MyProps": "ss",
    }


def test_create_trigger_event():
    event_dict = load_event("cloudformationCustomResourceCreate.json")
    handle_create_custom_resource(event_dict, LambdaContext())


def test_update_trigger_event():
    event_dict = load_event("cloudformationCustomResourceUpdate.json")
    handle_update_custom_resource(event_dict, LambdaContext())


def test_delete_trigger_event():
    event_dict = load_event("cloudformationCustomResourceDelete.json")
    handle_delete_custom_resource(event_dict, LambdaContext())


def test_validate_create_event_does_not_conform_with_model():
    event = {"invalid": "event"}
    with pytest.raises(ValidationError):
        handle_create_custom_resource(event, LambdaContext())


def test_validate_update_event_does_not_conform_with_model():
    event = {"invalid": "event"}
    with pytest.raises(ValidationError):
        handle_update_custom_resource(event, LambdaContext())


def test_validate_delete_event_does_not_conform_with_model():
    event = {"invalid": "event"}
    with pytest.raises(ValidationError):
        handle_delete_custom_resource(event, LambdaContext())


class MyModel(BaseModel):
    MyProps: str


class MyCustomResource(CloudFormationCustomResourceCreateModel):
    resource_properties: MyModel = Field(..., alias="ResourceProperties")


@event_parser(model=MyCustomResource)
def handle_create_custom_resource_extended_model(event: MyCustomResource, _: LambdaContext):
    assert event.request_type == "Create"
    assert event.request_id == "xxxxx-d2a0-4dfb-ab1f-xxxxxx"
    assert event.service_token == "arn:aws:lambda:us-east-1:xxx:function:xxxx-CrbuiltinfunctionidProvi-2vKAalSppmKe"
    assert (
        str(event.response_url)
        == "https://cloudformation-custom-resource-response-useast1.s3.amazonaws.com/7F%7Cb1f50fdfc25f3b"
    )
    assert event.stack_id == "arn:aws:cloudformation:us-east-1:xxxx:stack/xxxx/271845b0-f2e8-11ed-90ac-0eeb25b8ae21"
    assert event.logical_resource_id == "xxxxxxxxx"
    assert event.resource_type == "Custom::MyType"
    assert event.resource_properties.MyProps == "ss"


def test_create_trigger_event_custom_model():
    event_dict = load_event("cloudformationCustomResourceCreate.json")
    handle_create_custom_resource_extended_model(event_dict, LambdaContext())
