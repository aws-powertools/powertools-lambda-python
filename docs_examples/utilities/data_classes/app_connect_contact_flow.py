from aws_lambda_powertools.utilities.data_classes.connect_contact_flow_event import (
    ConnectContactFlowChannel,
    ConnectContactFlowEndpointType,
    ConnectContactFlowEvent,
    ConnectContactFlowInitiationMethod,
)


def lambda_handler(event, context):
    event: ConnectContactFlowEvent = ConnectContactFlowEvent(event)
    assert event.contact_data.attributes == {"Language": "en-US"}
    assert event.contact_data.channel == ConnectContactFlowChannel.VOICE
    assert event.contact_data.customer_endpoint.endpoint_type == ConnectContactFlowEndpointType.TELEPHONE_NUMBER
    assert event.contact_data.initiation_method == ConnectContactFlowInitiationMethod.API
