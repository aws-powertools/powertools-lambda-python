from aws_lambda_powertools.utilities.parser import envelopes, parse
from aws_lambda_powertools.utilities.parser.models import (
    APIGatewayWebSocketConnectEventModel,
    APIGatewayWebSocketDisconnectEventModel,
    APIGatewayWebSocketMessageEventModel,
)
from tests.functional.utils import load_event
from tests.unit.parser._pydantic.schemas import MyApiGatewayWebSocketBusiness


def test_apigw_websocket_message_event_with_envelope():
    raw_event = load_event("apiGatewayWebSocketApiMessage.json")
    raw_event["body"] = '{"action": "chat", "message": "Hello Ran"}'
    parsed_event: MyApiGatewayWebSocketBusiness = parse(
        event=raw_event,
        model=MyApiGatewayWebSocketBusiness,
        envelope=envelopes.ApiGatewayWebSocketEnvelope,
    )

    assert parsed_event.message == "Hello Ran"
    assert parsed_event.action == "chat"


def test_apigw_websocket_message_event():
    raw_event = load_event("apiGatewayWebSocketApiMessage.json")
    parsed_event: APIGatewayWebSocketMessageEventModel = APIGatewayWebSocketMessageEventModel(**raw_event)

    request_context = parsed_event.request_context
    assert request_context.api_id == raw_event["requestContext"]["apiId"]
    assert request_context.domain_name == raw_event["requestContext"]["domainName"]
    assert request_context.extended_request_id == raw_event["requestContext"]["extendedRequestId"]

    identity = request_context.identity
    assert str(identity.source_ip) == f'{raw_event["requestContext"]["identity"]["sourceIp"]}/32'

    assert request_context.request_id == raw_event["requestContext"]["requestId"]
    assert request_context.request_time == raw_event["requestContext"]["requestTime"]
    convert_time = int(round(request_context.request_time_epoch.timestamp() * 1000))
    assert convert_time == 1731332746514
    assert request_context.stage == raw_event["requestContext"]["stage"]
    convert_time = int(round(request_context.connected_at.timestamp() * 1000))
    assert convert_time == 1731332735513
    assert request_context.connection_id == raw_event["requestContext"]["connectionId"]
    assert request_context.event_type == raw_event["requestContext"]["eventType"]
    assert request_context.message_direction == raw_event["requestContext"]["messageDirection"]
    assert request_context.message_id == raw_event["requestContext"]["messageId"]
    assert request_context.route_key == raw_event["requestContext"]["routeKey"]

    assert parsed_event.body == raw_event["body"]
    assert parsed_event.is_base64_encoded == raw_event["isBase64Encoded"]


# not sure you can send an empty body TBH but it was a test in api gw so i kept it here, needs verification
def test_apigw_websocket_message_event_empty_body():
    event = load_event("apiGatewayWebSocketApiMessage.json")
    event["body"] = None
    parse(event=event, model=APIGatewayWebSocketMessageEventModel)


def test_apigw_websocket_connect_event():
    raw_event = load_event("apiGatewayWebSocketApiConnect.json")
    parsed_event: APIGatewayWebSocketConnectEventModel = APIGatewayWebSocketConnectEventModel(**raw_event)

    request_context = parsed_event.request_context
    assert request_context.api_id == raw_event["requestContext"]["apiId"]
    assert request_context.domain_name == raw_event["requestContext"]["domainName"]
    assert request_context.extended_request_id == raw_event["requestContext"]["extendedRequestId"]

    identity = request_context.identity
    assert str(identity.source_ip) == f'{raw_event["requestContext"]["identity"]["sourceIp"]}/32'

    assert request_context.request_id == raw_event["requestContext"]["requestId"]
    assert request_context.request_time == raw_event["requestContext"]["requestTime"]
    convert_time = int(round(request_context.request_time_epoch.timestamp() * 1000))
    assert convert_time == 1731324924561
    assert request_context.stage == raw_event["requestContext"]["stage"]
    convert_time = int(round(request_context.connected_at.timestamp() * 1000))
    assert convert_time == 1731324924553
    assert request_context.connection_id == raw_event["requestContext"]["connectionId"]
    assert request_context.event_type == raw_event["requestContext"]["eventType"]
    assert request_context.message_direction == raw_event["requestContext"]["messageDirection"]
    assert request_context.route_key == raw_event["requestContext"]["routeKey"]

    assert parsed_event.is_base64_encoded == raw_event["isBase64Encoded"]
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.multi_value_headers == raw_event["multiValueHeaders"]


def test_apigw_websocket_disconnect_event():
    raw_event = load_event("apiGatewayWebSocketApiDisconnect.json")
    parsed_event: APIGatewayWebSocketDisconnectEventModel = APIGatewayWebSocketDisconnectEventModel(**raw_event)

    request_context = parsed_event.request_context
    assert request_context.api_id == raw_event["requestContext"]["apiId"]
    assert request_context.domain_name == raw_event["requestContext"]["domainName"]
    assert request_context.extended_request_id == raw_event["requestContext"]["extendedRequestId"]

    identity = request_context.identity
    assert str(identity.source_ip) == f'{raw_event["requestContext"]["identity"]["sourceIp"]}/32'

    assert request_context.request_id == raw_event["requestContext"]["requestId"]
    assert request_context.request_time == raw_event["requestContext"]["requestTime"]
    convert_time = int(round(request_context.request_time_epoch.timestamp() * 1000))
    assert convert_time == 1731333109875
    assert request_context.stage == raw_event["requestContext"]["stage"]
    convert_time = int(round(request_context.connected_at.timestamp() * 1000))
    assert convert_time == 1731332735513
    assert request_context.connection_id == raw_event["requestContext"]["connectionId"]
    assert request_context.event_type == raw_event["requestContext"]["eventType"]
    assert request_context.message_direction == raw_event["requestContext"]["messageDirection"]
    assert request_context.route_key == raw_event["requestContext"]["routeKey"]
    assert request_context.disconnect_reason == raw_event["requestContext"]["disconnectReason"]
    assert request_context.disconnect_status_code == raw_event["requestContext"]["disconnectStatusCode"]

    assert parsed_event.is_base64_encoded == raw_event["isBase64Encoded"]
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.multi_value_headers == raw_event["multiValueHeaders"]
