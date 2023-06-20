from aws_lambda_powertools.utilities.data_classes import LambdaFunctionUrlEvent
from tests.functional.utils import load_event


def test_lambda_function_url_event():
    event = LambdaFunctionUrlEvent(load_event("lambdaFunctionUrlEvent.json"))

    assert event.version == "2.0"
    assert event.route_key == "$default"

    assert event.path == "/"
    assert event.raw_query_string == ""

    assert event.cookies is None

    headers = event.headers
    assert len(headers) == 20

    assert event.query_string_parameters is None

    assert event.is_base64_encoded is False
    assert event.body is None
    assert event.path_parameters is None
    assert event.stage_variables is None
    assert event.http_method == "GET"

    request_context = event.request_context

    assert request_context.account_id == "anonymous"
    assert request_context.api_id is not None
    assert request_context.domain_name == "<url-id>.lambda-url.us-east-1.on.aws"
    assert request_context.domain_prefix == "<url-id>"
    assert request_context.request_id == "id"
    assert request_context.route_key == "$default"
    assert request_context.stage == "$default"
    assert request_context.time is not None
    assert request_context.time_epoch == 1659687279885
    assert request_context.authentication is None

    http = request_context.http
    assert http.method == "GET"
    assert http.path == "/"
    assert http.protocol == "HTTP/1.1"
    assert http.source_ip == "123.123.123.123"
    assert http.user_agent == "agent"

    assert request_context.authorizer is None


def test_lambda_function_url_event_iam():
    event = LambdaFunctionUrlEvent(load_event("lambdaFunctionUrlIAMEvent.json"))

    assert event.version == "2.0"
    assert event.route_key == "$default"

    assert event.path == "/my/path"
    assert event.raw_query_string == "parameter1=value1&parameter1=value2&parameter2=value"

    cookies = event.cookies
    assert len(cookies) == 2
    assert cookies[0] == "cookie1"

    headers = event.headers
    assert len(headers) == 2

    query_string_parameters = event.query_string_parameters
    assert len(query_string_parameters) == 2
    assert query_string_parameters.get("parameter2") == "value"

    assert event.is_base64_encoded is False
    assert event.body == "Hello from client!"
    assert event.decoded_body == event.body
    assert event.path_parameters is None
    assert event.stage_variables is None
    assert event.http_method == "POST"

    request_context = event.request_context

    assert request_context.account_id == "123456789012"
    assert request_context.api_id is not None
    assert request_context.domain_name == "<url-id>.lambda-url.us-west-2.on.aws"
    assert request_context.domain_prefix == "<url-id>"
    assert request_context.request_id == "id"
    assert request_context.route_key == "$default"
    assert request_context.stage == "$default"
    assert request_context.time is not None
    assert request_context.time_epoch == 1583348638390
    assert request_context.authentication is None

    http = request_context.http
    assert http.method == "POST"
    assert http.path == "/my/path"
    assert http.protocol == "HTTP/1.1"
    assert http.source_ip == "123.123.123.123"
    assert http.user_agent == "agent"

    authorizer = request_context.authorizer
    assert authorizer is not None
    assert authorizer.jwt_claim is None
    assert authorizer.jwt_scopes is None
    assert authorizer.get_lambda is None

    iam = authorizer.iam
    assert iam is not None
    assert iam.access_key is not None
    assert iam.account_id == "111122223333"
    assert iam.caller_id is not None
    assert iam.cognito_amr is None
    assert iam.cognito_identity_id is None
    assert iam.cognito_identity_pool_id is None
    assert iam.principal_org_id is None
    assert iam.user_id is not None
    assert iam.user_arn == "arn:aws:iam::111122223333:user/example-user"
