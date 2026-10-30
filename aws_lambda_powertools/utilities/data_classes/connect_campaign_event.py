from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper

if TYPE_CHECKING:
    from collections.abc import Iterator


class ConnectOutboundCampaignContext(DictWrapper):
    """Campaign and execution context details."""

    @property
    def campaign_id(self) -> str:
        """The identifier of the campaign."""
        return self["CampaignId"]

    @property
    def run_id(self) -> str:
        """The identifier of the campaign run."""
        return self["RunId"]

    @property
    def action_id(self) -> str:
        """The identifier of the activity or action block."""
        return self["ActionId"]

    @property
    def campaign_name(self) -> str:
        """The name of the campaign."""
        return self["CampaignName"]


class ConnectOutboundCampaignInvocationMetadata(DictWrapper):
    """Invocation metadata containing the campaign context."""

    @property
    def campaign_context(self) -> ConnectOutboundCampaignContext:
        """Metadata for the campaign and execution context."""
        return ConnectOutboundCampaignContext(self["CampaignContext"])


class ConnectOutboundCampaignCustomerProfile(DictWrapper):
    """Customer profile record within an outbound campaign batch."""

    @property
    def profile_id(self) -> str:
        """The identifier of the customer profile."""
        return self["ProfileId"]

    @property
    def customer_data(self) -> str:
        """The JSON-encoded customer data string configured in the campaign."""
        return self["CustomerData"]

    @cached_property
    def json_customer_data(self) -> Any:
        """Parsed JSON object of customer data."""
        return self._json_deserializer(self["CustomerData"])

    @property
    def idempotency_token(self) -> str:
        """The idempotency token for deduplication."""
        return self["IdempotencyToken"]


class ConnectOutboundCampaignItems(DictWrapper):
    """Container for customer profile items."""

    @property
    def customer_profiles(self) -> Iterator[ConnectOutboundCampaignCustomerProfile]:
        """Iterate over customer profiles."""
        for item in self["CustomerProfiles"]:
            yield ConnectOutboundCampaignCustomerProfile(item)


class ConnectOutboundCampaignsEvent(DictWrapper):
    """Amazon Connect Outbound Campaigns custom action event.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/connect/latest/adminguide/lambda-invoke-functions.html
    """

    @property
    def invocation_metadata(self) -> ConnectOutboundCampaignInvocationMetadata:
        """Invocation metadata including campaign context."""
        return ConnectOutboundCampaignInvocationMetadata(self["InvocationMetadata"])

    @property
    def items_payload(self) -> ConnectOutboundCampaignItems:
        """Items payload containing customer profiles."""
        return ConnectOutboundCampaignItems(self["Items"])

    @property
    def customer_profiles(self) -> Iterator[ConnectOutboundCampaignCustomerProfile]:
        """Convenience accessor to iterate directly over customer profiles."""
        return self.items_payload.customer_profiles
