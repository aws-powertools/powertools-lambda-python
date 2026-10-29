from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ConnectCampaignContextModel(BaseModel):
    """Campaign context details model."""

    campaign_id: str = Field(..., alias="CampaignId")
    run_id: str = Field(..., alias="RunId")
    action_id: str = Field(..., alias="ActionId")
    campaign_name: str = Field(..., alias="CampaignName")


class ConnectInvocationMetadataModel(BaseModel):
    """Invocation metadata container model."""

    campaign_context: ConnectCampaignContextModel = Field(..., alias="CampaignContext")


class ConnectCustomerProfileModel(BaseModel):
    """Customer profile record model.

    CustomerData is campaign-defined and can be a raw JSON string or structured object.
    Users can inherit from this model to provide a typed schema for CustomerData.
    """

    profile_id: str = Field(..., alias="ProfileId")
    customer_data: Any = Field(..., alias="CustomerData")
    idempotency_token: str = Field(..., alias="IdempotencyToken")


class ConnectItemsModel(BaseModel):
    """Container for customer profiles."""

    customer_profiles: list[ConnectCustomerProfileModel] = Field(..., alias="CustomerProfiles")


class ConnectOutboundCampaignsEventModel(BaseModel):
    """Amazon Connect Outbound Campaigns custom action event model.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/connect/latest/adminguide/lambda-invoke-functions.html
    """

    invocation_metadata: ConnectInvocationMetadataModel = Field(..., alias="InvocationMetadata")
    items: ConnectItemsModel = Field(..., alias="Items")
