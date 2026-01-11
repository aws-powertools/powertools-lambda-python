from __future__ import annotations

from urllib.parse import quote

from aws_lambda_powertools.utilities.data_classes import ALBEvent
from tests.functional.utils import load_event


def test_alb_event():
    raw_event = load_event("albEvent.json")
    parsed_event = ALBEvent(raw_event)

    assert parsed_event.request_context.elb_target_group_arn == raw_event["requestContext"]["elb"]["targetGroupArn"]
    assert parsed_event.http_method == raw_event["httpMethod"]
    assert parsed_event.path == raw_event["path"]
    assert parsed_event.query_string_parameters == raw_event["queryStringParameters"]
    assert parsed_event.headers == raw_event["headers"]

    assert parsed_event.multi_value_query_string_parameters == raw_event.get("multiValueQueryStringParameters", {})

    assert parsed_event.multi_value_headers == (raw_event.get("multiValueHeaders") or {})
    assert parsed_event.body == raw_event["body"]
    assert parsed_event.is_base64_encoded == raw_event["isBase64Encoded"]


def test_alb_event_decode_query_parameters():
    expected_key = "this is a key"
    expected_value = "single value"
    raw_event = load_event("albEvent.json")
    raw_event["queryStringParameters"] = {quote(expected_key): quote(expected_value)}
    # Without decode_query_parameters, the key and value are not decoded
    parsed_event = ALBEvent(raw_event)
    assert parsed_event.resolved_query_string_parameters != {expected_key: [expected_value]}
    assert parsed_event.resolved_query_string_parameters == {quote(expected_key): [quote(expected_value)]}

    # With decode_query_parameters, the key and value are not decoded
    parsed_event.decode_query_parameters = True
    assert parsed_event.resolved_query_string_parameters == {expected_key: [expected_value]}


def test_alb_event_decode_multi_value_query_parameters():
    expected_key = "this is a key"
    expected_values = ["first value", "second value"]

    raw_event = load_event("albMultiValueQueryStringEvent.json")
    raw_event["multiValueQueryStringParameters"] = {quote(expected_key): [quote(v) for v in expected_values]}
    # Without decode_query_parameters, the key and value are not decoded
    parsed_event = ALBEvent(raw_event)
    assert parsed_event.resolved_query_string_parameters != {expected_key: expected_values}
    assert parsed_event.resolved_query_string_parameters == {quote(expected_key): [quote(v) for v in expected_values]}

    # With decode_query_parameters, the key and value are not decoded
    parsed_event.decode_query_parameters = True
    assert parsed_event.resolved_query_string_parameters == {expected_key: expected_values}
