from aws_lambda_powertools.utilities.data_classes import (
    ConnectOutboundCampaignsEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=ConnectOutboundCampaignsEvent)
def lambda_handler(event: ConnectOutboundCampaignsEvent, context: LambdaContext):
    campaign = event.invocation_metadata.campaign_context
    print(f"Processing campaign {campaign.campaign_name} (ID: {campaign.campaign_id})")

    for profile in event.customer_profiles:
        profile_id = profile.profile_id
        # json_customer_data deserializes the embedded JSON string
        customer_info = profile.json_customer_data
        print(f"Customer {profile_id}: {customer_info}")
