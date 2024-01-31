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
    assert parsed_event.multi_value_query_string_parameters == raw_event.get("multiValueQueryStringParameters")
    assert parsed_event.multi_value_headers == raw_event.get("multiValueHeaders")
    assert parsed_event.body == raw_event["body"]
    assert parsed_event.is_base64_encoded == raw_event["isBase64Encoded"]
