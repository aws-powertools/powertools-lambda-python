from aws_lambda_powertools.utilities.data_classes import ALBEvent
from tests.functional.utils import load_event


def test_alb_event():
    event = ALBEvent(load_event("albEvent.json"))
    assert event.request_context.elb_target_group_arn == event["requestContext"]["elb"]["targetGroupArn"]
    assert event.http_method == event["httpMethod"]
    assert event.path == event["path"]
    assert event.query_string_parameters == event["queryStringParameters"]
    assert event.headers == event["headers"]
    assert event.multi_value_query_string_parameters == event.get("multiValueQueryStringParameters")
    assert event.multi_value_headers == event.get("multiValueHeaders")
    assert event.body == event["body"]
    assert event.is_base64_encoded == event["isBase64Encoded"]
