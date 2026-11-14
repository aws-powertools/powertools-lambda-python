from __future__ import annotations

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

    CustomerData is a JSON string with campaign-defined key-value pairs. To get a typed object,
    inherit from this model and declare the field as ``Json[YourModel]`` so Pydantic decodes the string:

        class Profile(ConnectCustomerProfileModel):
            customer_data: Json[CustomerPayload] = Field(..., alias="CustomerData")
    """

    profile_id: str = Field(..., alias="ProfileId")
    customer_data: str = Field(..., alias="CustomerData")
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
