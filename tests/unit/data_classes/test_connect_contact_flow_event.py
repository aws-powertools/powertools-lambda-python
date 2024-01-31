from aws_lambda_powertools.utilities.data_classes.connect_contact_flow_event import (
    ConnectContactFlowChannel,
    ConnectContactFlowEndpointType,
    ConnectContactFlowEvent,
    ConnectContactFlowInitiationMethod,
)
from tests.functional.utils import load_event


def test_connect_contact_flow_event_min():
    raw_event = load_event("connectContactFlowEventMin.json")
    parsed_event = ConnectContactFlowEvent(raw_event)

    contact_data_raw = raw_event["Details"]["ContactData"]

    assert parsed_event.contact_data.attributes == {}
    assert parsed_event.contact_data.channel == ConnectContactFlowChannel.VOICE
    assert parsed_event.contact_data.contact_id == contact_data_raw["ContactId"]
    assert parsed_event.contact_data.customer_endpoint is None
    assert parsed_event.contact_data.initial_contact_id == contact_data_raw["InitialContactId"]
    assert parsed_event.contact_data.initiation_method == ConnectContactFlowInitiationMethod.API
    assert parsed_event.contact_data.instance_arn == contact_data_raw["InstanceARN"]
    assert parsed_event.contact_data.media_streams.customer.audio.start_fragment_number is None
    assert parsed_event.contact_data.media_streams.customer.audio.start_timestamp is None
    assert parsed_event.contact_data.media_streams.customer.audio.stream_arn is None
    assert parsed_event.contact_data.previous_contact_id == contact_data_raw["PreviousContactId"]
    assert parsed_event.contact_data.queue is None
    assert parsed_event.contact_data.system_endpoint is None
    assert parsed_event.parameters == {}


def test_connect_contact_flow_event_all():
    raw_event = load_event("connectContactFlowEventAll.json")
    parsed_event = ConnectContactFlowEvent(raw_event)

    contact_data_raw = raw_event["Details"]["ContactData"]

    assert parsed_event.contact_data.attributes == {"Language": "en-US"}
    assert parsed_event.contact_data.channel == ConnectContactFlowChannel.VOICE
    assert parsed_event.contact_data.contact_id == contact_data_raw["ContactId"]
    assert parsed_event.contact_data.customer_endpoint is not None
    assert parsed_event.contact_data.customer_endpoint.address == contact_data_raw["CustomerEndpoint"]["Address"]
    assert parsed_event.contact_data.customer_endpoint.endpoint_type == ConnectContactFlowEndpointType.TELEPHONE_NUMBER
    assert parsed_event.contact_data.initial_contact_id == contact_data_raw["InitialContactId"]
    assert parsed_event.contact_data.initiation_method == ConnectContactFlowInitiationMethod.API
    assert parsed_event.contact_data.instance_arn == contact_data_raw["InstanceARN"]
    assert (
        parsed_event.contact_data.media_streams.customer.audio.start_fragment_number
        == contact_data_raw["MediaStreams"]["Customer"]["Audio"]["StartFragmentNumber"]
    )
    assert (
        parsed_event.contact_data.media_streams.customer.audio.start_timestamp
        == contact_data_raw["MediaStreams"]["Customer"]["Audio"]["StartTimestamp"]
    )
    assert (
        parsed_event.contact_data.media_streams.customer.audio.stream_arn
        == contact_data_raw["MediaStreams"]["Customer"]["Audio"]["StreamARN"]
    )
    assert parsed_event.contact_data.previous_contact_id == contact_data_raw["PreviousContactId"]
    assert parsed_event.contact_data.queue is not None
    assert parsed_event.contact_data.queue.arn == contact_data_raw["Queue"]["ARN"]
    assert parsed_event.contact_data.queue.name == contact_data_raw["Queue"]["Name"]
    assert parsed_event.contact_data.system_endpoint is not None
    assert parsed_event.contact_data.system_endpoint.address == contact_data_raw["SystemEndpoint"]["Address"]
    assert parsed_event.contact_data.system_endpoint.endpoint_type == ConnectContactFlowEndpointType.TELEPHONE_NUMBER
    assert parsed_event.parameters == {"ParameterOne": "One", "ParameterTwo": "Two"}
