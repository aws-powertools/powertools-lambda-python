from aws_lambda_powertools.utilities.data_classes.connect_contact_flow_event import (
    ConnectContactFlowChannel,
    ConnectContactFlowEndpointType,
    ConnectContactFlowEvent,
    ConnectContactFlowInitiationMethod,
)
from tests.functional.utils import load_event


def test_connect_contact_flow_event_min():
    event = ConnectContactFlowEvent(load_event("connectContactFlowEventMin.json"))

    assert event.contact_data.attributes == {}
    assert event.contact_data.channel == ConnectContactFlowChannel.VOICE
    assert event.contact_data.contact_id == "5ca32fbd-8f92-46af-92a5-6b0f970f0efe"
    assert event.contact_data.customer_endpoint is None
    assert event.contact_data.initial_contact_id == "5ca32fbd-8f92-46af-92a5-6b0f970f0efe"
    assert event.contact_data.initiation_method == ConnectContactFlowInitiationMethod.API
    assert (
        event.contact_data.instance_arn
        == "arn:aws:connect:eu-central-1:123456789012:instance/9308c2a1-9bc6-4cea-8290-6c0b4a6d38fa"
    )
    assert event.contact_data.media_streams.customer.audio.start_fragment_number is None
    assert event.contact_data.media_streams.customer.audio.start_timestamp is None
    assert event.contact_data.media_streams.customer.audio.stream_arn is None
    assert event.contact_data.previous_contact_id == "5ca32fbd-8f92-46af-92a5-6b0f970f0efe"
    assert event.contact_data.queue is None
    assert event.contact_data.system_endpoint is None
    assert event.parameters == {}


def test_connect_contact_flow_event_all():
    event = ConnectContactFlowEvent(load_event("connectContactFlowEventAll.json"))

    assert event.contact_data.attributes == {"Language": "en-US"}
    assert event.contact_data.channel == ConnectContactFlowChannel.VOICE
    assert event.contact_data.contact_id == "5ca32fbd-8f92-46af-92a5-6b0f970f0efe"
    assert event.contact_data.customer_endpoint is not None
    assert event.contact_data.customer_endpoint.address == "+11234567890"
    assert event.contact_data.customer_endpoint.endpoint_type == ConnectContactFlowEndpointType.TELEPHONE_NUMBER
    assert event.contact_data.initial_contact_id == "5ca32fbd-8f92-46af-92a5-6b0f970f0efe"
    assert event.contact_data.initiation_method == ConnectContactFlowInitiationMethod.API
    assert (
        event.contact_data.instance_arn
        == "arn:aws:connect:eu-central-1:123456789012:instance/9308c2a1-9bc6-4cea-8290-6c0b4a6d38fa"
    )
    assert (
        event.contact_data.media_streams.customer.audio.start_fragment_number
        == "91343852333181432392682062622220590765191907586"
    )
    assert event.contact_data.media_streams.customer.audio.start_timestamp == "1565781909613"
    assert (
        event.contact_data.media_streams.customer.audio.stream_arn
        == "arn:aws:kinesisvideo:eu-central-1:123456789012:stream/"
        + "connect-contact-a3d73b84-ce0e-479a-a9dc-5637c9d30ac9/1565272947806"
    )
    assert event.contact_data.previous_contact_id == "5ca32fbd-8f92-46af-92a5-6b0f970f0efe"
    assert event.contact_data.queue is not None
    assert (
        event.contact_data.queue.arn
        == "arn:aws:connect:eu-central-1:123456789012:instance/9308c2a1-9bc6-4cea-8290-6c0b4a6d38fa/"
        + "queue/5cba7cbf-1ecb-4b6d-b8bd-fe91079b3fc8"
    )
    assert event.contact_data.queue.name == "QueueOne"
    assert event.contact_data.system_endpoint is not None
    assert event.contact_data.system_endpoint.address == "+11234567890"
    assert event.contact_data.system_endpoint.endpoint_type == ConnectContactFlowEndpointType.TELEPHONE_NUMBER
    assert event.parameters == {"ParameterOne": "One", "ParameterTwo": "Two"}
