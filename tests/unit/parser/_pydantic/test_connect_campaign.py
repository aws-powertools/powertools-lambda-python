import pytest
from pydantic import BaseModel, Field, ValidationError

from aws_lambda_powertools.utilities.parser import parse
from aws_lambda_powertools.utilities.parser.models import (
    ConnectCampaignContextModel,
    ConnectCustomerProfileModel,
    ConnectItemsModel,
    ConnectOutboundCampaignsEventModel,
)
from tests.functional.utils import load_event


class CustomerPayload(BaseModel):
    firstName: str
    lastName: str
    email: str


class CustomCustomerProfileModel(ConnectCustomerProfileModel):
    customer_data: CustomerPayload = Field(..., alias="CustomerData")


class CustomConnectItemsModel(ConnectItemsModel):
    customer_profiles: list[CustomCustomerProfileModel] = Field(..., alias="CustomerProfiles")


class CustomConnectOutboundCampaignsEventModel(ConnectOutboundCampaignsEventModel):
    items: CustomConnectItemsModel = Field(..., alias="Items")


def test_connect_outbound_campaigns_event_model():
    raw_event = load_event("connectOutboundCampaignsEvent.json")
    parsed: ConnectOutboundCampaignsEventModel = parse(
        event=raw_event,
        model=ConnectOutboundCampaignsEventModel,
    )

    context: ConnectCampaignContextModel = parsed.invocation_metadata.campaign_context
    assert context.campaign_id == "campaign-12345"
    assert context.run_id == "run-67890"
    assert context.action_id == "activity-abc123"
    assert context.campaign_name == "Welcome Campaign"

    profiles: list[ConnectCustomerProfileModel] = parsed.items.customer_profiles
    assert len(profiles) == 2

    assert profiles[0].profile_id == "customer-001"
    assert profiles[0].customer_data == '{"firstName":"John","lastName":"Doe","email":"john.doe@example.com"}'
    assert profiles[0].idempotency_token == "token-xyz789"

    assert profiles[1].profile_id == "customer-002"
    assert profiles[1].customer_data == '{"firstName":"Jane","lastName":"Smith","email":"jane.smith@example.com"}'
    assert profiles[1].idempotency_token == "token-abc456"


def test_connect_outbound_campaigns_event_missing_required_fields():
    raw_event = load_event("connectOutboundCampaignsEvent.json")
    del raw_event["InvocationMetadata"]

    with pytest.raises(ValidationError):
        parse(event=raw_event, model=ConnectOutboundCampaignsEventModel)


def test_connect_outbound_campaigns_event_with_custom_typed_customer_data():
    raw_event = load_event("connectOutboundCampaignsEvent.json")
    # Simulate parsed JSON or custom dict payload for customer_data
    raw_event["Items"]["CustomerProfiles"][0]["CustomerData"] = {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com",
    }
    raw_event["Items"]["CustomerProfiles"][1]["CustomerData"] = {
        "firstName": "Jane",
        "lastName": "Smith",
        "email": "jane.smith@example.com",
    }

    parsed = parse(event=raw_event, model=CustomConnectOutboundCampaignsEventModel)
    profile = parsed.items.customer_profiles[0]
    assert profile.customer_data.firstName == "John"
    assert profile.customer_data.lastName == "Doe"
    assert profile.customer_data.email == "john.doe@example.com"
