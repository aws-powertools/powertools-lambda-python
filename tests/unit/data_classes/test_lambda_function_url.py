from aws_lambda_powertools.utilities.data_classes import LambdaFunctionUrlEvent
from tests.functional.utils import load_event


def test_lambda_function_url_event():
    raw_event = load_event("lambdaFunctionUrlEvent.json")
    parsed_event = LambdaFunctionUrlEvent(raw_event)

    assert parsed_event.version == raw_event["version"]
    assert parsed_event.route_key == raw_event["routeKey"]

    assert parsed_event.path == raw_event["rawPath"]
    assert parsed_event.raw_query_string == raw_event["rawQueryString"]

    assert parsed_event.cookies is None

    headers = parsed_event.headers
    assert len(headers) == 20

    assert parsed_event.query_string_parameters is None

    assert parsed_event.is_base64_encoded is False
    assert parsed_event.body is None
    assert parsed_event.path_parameters is None
    assert parsed_event.stage_variables is None
    assert parsed_event.http_method == raw_event["requestContext"]["http"]["method"]

    request_context = parsed_event.request_context
    request_context_raw = raw_event["requestContext"]

    assert request_context.account_id == request_context_raw["accountId"]
    assert request_context.api_id == request_context_raw["apiId"]
    assert request_context.domain_name == request_context_raw["domainName"]
    assert request_context.domain_prefix == request_context_raw["domainPrefix"]
    assert request_context.request_id == request_context_raw["requestId"]
    assert request_context.route_key == request_context_raw["routeKey"]
    assert request_context.stage == request_context_raw["stage"]
    assert request_context.time == request_context_raw["time"]
    assert request_context.time_epoch == request_context_raw["timeEpoch"]
    assert request_context.authentication is None

    http = request_context.http
    http_raw = raw_event["requestContext"]["http"]
    assert http.method == http_raw["method"]
    assert http.path == http_raw["path"]
    assert http.protocol == http_raw["protocol"]
    assert http.source_ip == http_raw["sourceIp"]
    assert http.user_agent == http_raw["userAgent"]

    assert request_context.authorizer is None


def test_lambda_function_url_event_iam():
    raw_event = load_event("lambdaFunctionUrlIAMEvent.json")
    parsed_event = LambdaFunctionUrlEvent(raw_event)

    assert parsed_event.version == raw_event["version"]
    assert parsed_event.route_key == raw_event["routeKey"]

    assert parsed_event.path == raw_event["rawPath"]
    assert parsed_event.raw_query_string == raw_event["rawQueryString"]

    headers = parsed_event.headers
    assert len(headers) == 2

    cookies = parsed_event.cookies
    assert len(cookies) == 2
    assert cookies[0] == "cookie1"

    query_string_parameters = parsed_event.query_string_parameters
    assert len(query_string_parameters) == 2
    assert query_string_parameters.get("parameter2") == raw_event["queryStringParameters"]["parameter2"]

    assert parsed_event.is_base64_encoded is False
    assert parsed_event.body == raw_event["body"]
    assert parsed_event.decoded_body == raw_event["body"]
    assert parsed_event.path_parameters is None
    assert parsed_event.stage_variables is None
    assert parsed_event.http_method == raw_event["requestContext"]["http"]["method"]

    request_context = parsed_event.request_context
    request_context_raw = raw_event["requestContext"]

    assert request_context.account_id == request_context_raw["accountId"]
    assert request_context.api_id == request_context_raw["apiId"]
    assert request_context.domain_name == request_context_raw["domainName"]
    assert request_context.domain_prefix == request_context_raw["domainPrefix"]
    assert request_context.request_id == request_context_raw["requestId"]
    assert request_context.route_key == request_context_raw["routeKey"]
    assert request_context.stage == request_context_raw["stage"]
    assert request_context.time == request_context_raw["time"]
    assert request_context.time_epoch == request_context_raw["timeEpoch"]
    assert request_context.authentication is None

    http = request_context.http
    http_raw = raw_event["requestContext"]["http"]
    assert http.method == http_raw["method"]
    assert http.path == http_raw["path"]
    assert http.protocol == http_raw["protocol"]
    assert http.source_ip == http_raw["sourceIp"]
    assert http.user_agent == http_raw["userAgent"]

    authorizer = request_context.authorizer
    assert authorizer is not None
    assert authorizer.jwt_claim is None
    assert authorizer.jwt_scopes is None
    assert authorizer.get_lambda is None

    iam = authorizer.iam
    iam_raw = raw_event["requestContext"]["authorizer"]["iam"]
    assert iam is not None
    assert iam.access_key == iam_raw["accessKey"]
    assert iam.account_id == iam_raw["accountId"]
    assert iam.caller_id == iam_raw["callerId"]
    assert iam.cognito_amr is None
    assert iam.cognito_identity_id is None
    assert iam.cognito_identity_pool_id is None
    assert iam.principal_org_id is None
    assert iam.user_id == iam_raw["userId"]
    assert iam.user_arn == iam_raw["userArn"]
