from aws_lambda_powertools.utilities.data_classes import ConnectOutboundCampaignsEvent
from tests.functional.utils import load_event


def test_connect_outbound_campaigns_event():
    raw_event = load_event("connectOutboundCampaignsEvent.json")
    event = ConnectOutboundCampaignsEvent(raw_event)

    # Invocation metadata
    invoc_meta = event.invocation_metadata
    campaign_context = invoc_meta.campaign_context

    assert campaign_context.campaign_id == "campaign-12345"
    assert campaign_context.run_id == "run-67890"
    assert campaign_context.action_id == "activity-abc123"
    assert campaign_context.campaign_name == "Welcome Campaign"

    # Items and customer profiles via items_payload
    profiles = list(event.items_payload.customer_profiles)
    assert len(profiles) == 2

    # Direct convenience accessor
    assert len(list(event.customer_profiles)) == 2

    # First profile
    p1 = profiles[0]
    assert p1.profile_id == "customer-001"
    assert p1.customer_data == '{"firstName":"John","lastName":"Doe","email":"john.doe@example.com"}'
    assert p1.json_customer_data == {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com",
    }
    assert p1.idempotency_token == "token-xyz789"

    # Second profile
    p2 = profiles[1]
    assert p2.profile_id == "customer-002"
    assert p2.customer_data == '{"firstName":"Jane","lastName":"Smith","email":"jane.smith@example.com"}'
    assert p2.json_customer_data == {
        "firstName": "Jane",
        "lastName": "Smith",
        "email": "jane.smith@example.com",
    }
    assert p2.idempotency_token == "token-abc456"
