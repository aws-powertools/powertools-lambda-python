import json

from aws_lambda_powertools.utilities.data_classes import APIGatewayWebSocketEvent
from tests.functional.utils import load_event


def test_connect_api_gateway_websocket_event():
    raw_event = load_event("apiGatewayWebSocketApiConnect.json")
    parsed_event = APIGatewayWebSocketEvent(raw_event)

    assert parsed_event.is_base64_encoded is False
    assert parsed_event.body is None
    assert parsed_event.decoded_body is None
    assert parsed_event.json_body is None
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.multi_value_headers == raw_event["multiValueHeaders"]

    request_context = parsed_event.request_context
    request_context_raw = raw_event["requestContext"]
    assert request_context.route_key == request_context_raw["routeKey"]
    assert request_context.disconnect_status_code is None
    assert request_context.message_id is None
    assert request_context.event_type == request_context_raw["eventType"]
    assert request_context.extended_request_id == request_context_raw["extendedRequestId"]
    assert request_context.request_time == request_context_raw["requestTime"]
    assert request_context.message_direction == request_context_raw["messageDirection"]
    assert request_context.disconnect_reason is None
    assert request_context.stage == request_context_raw["stage"]
    assert request_context.connected_at == request_context_raw["connectedAt"]
    assert request_context.request_time_epoch == request_context_raw["requestTimeEpoch"]
    assert request_context.request_id == request_context_raw["requestId"]
    assert request_context.domain_name == request_context_raw["domainName"]
    assert request_context.connection_id == request_context_raw["connectionId"]
    assert request_context.api_id == request_context_raw["apiId"]

    identity = request_context.identity
    identity_raw = request_context_raw["identity"]
    assert identity.source_ip == identity_raw["sourceIp"]
    assert identity.user_agent is None


def test_disconnect_api_gateway_websocket_event():
    raw_event = load_event("apiGatewayWebSocketApiDisconnect.json")
    parsed_event = APIGatewayWebSocketEvent(raw_event)

    assert parsed_event.is_base64_encoded is False
    assert parsed_event.body is None
    assert parsed_event.decoded_body is None
    assert parsed_event.json_body is None
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.multi_value_headers == raw_event["multiValueHeaders"]

    request_context = parsed_event.request_context
    request_context_raw = raw_event["requestContext"]
    assert request_context.route_key == request_context_raw["routeKey"]
    assert request_context.disconnect_status_code == request_context_raw["disconnectStatusCode"]
    assert request_context.message_id is None
    assert request_context.event_type == request_context_raw["eventType"]
    assert request_context.extended_request_id == request_context_raw["extendedRequestId"]
    assert request_context.request_time == request_context_raw["requestTime"]
    assert request_context.message_direction == request_context_raw["messageDirection"]
    assert request_context.disconnect_reason == request_context_raw["disconnectReason"]
    assert request_context.stage == request_context_raw["stage"]
    assert request_context.connected_at == request_context_raw["connectedAt"]
    assert request_context.request_time_epoch == request_context_raw["requestTimeEpoch"]
    assert request_context.request_id == request_context_raw["requestId"]
    assert request_context.domain_name == request_context_raw["domainName"]
    assert request_context.connection_id == request_context_raw["connectionId"]
    assert request_context.api_id == request_context_raw["apiId"]

    identity = request_context.identity
    identity_raw = request_context_raw["identity"]
    assert identity.source_ip == identity_raw["sourceIp"]
    assert identity.user_agent is None


def test_message_api_gateway_websocket_event():
    raw_event = load_event("apiGatewayWebSocketApiMessage.json")
    parsed_event = APIGatewayWebSocketEvent(raw_event)

    assert parsed_event.is_base64_encoded is False
    assert parsed_event.body == raw_event["body"]
    assert parsed_event.decoded_body == raw_event["body"]
    assert parsed_event.json_body == json.loads(raw_event["body"])
    assert parsed_event.headers == {}
    assert parsed_event.multi_value_headers == {}

    request_context = parsed_event.request_context
    request_context_raw = raw_event["requestContext"]
    assert request_context.route_key == request_context_raw["routeKey"]
    assert request_context.disconnect_status_code is None
    assert request_context.message_id == request_context_raw["messageId"]
    assert request_context.event_type == request_context_raw["eventType"]
    assert request_context.extended_request_id == request_context_raw["extendedRequestId"]
    assert request_context.request_time == request_context_raw["requestTime"]
    assert request_context.message_direction == request_context_raw["messageDirection"]
    assert request_context.disconnect_reason is None
    assert request_context.stage == request_context_raw["stage"]
    assert request_context.connected_at == request_context_raw["connectedAt"]
    assert request_context.request_time_epoch == request_context_raw["requestTimeEpoch"]
    assert request_context.request_id == request_context_raw["requestId"]
    assert request_context.domain_name == request_context_raw["domainName"]
    assert request_context.connection_id == request_context_raw["connectionId"]
    assert request_context.api_id == request_context_raw["apiId"]

    identity = request_context.identity
    identity_raw = request_context_raw["identity"]
    assert identity.source_ip == identity_raw["sourceIp"]
    assert identity.user_agent is None
