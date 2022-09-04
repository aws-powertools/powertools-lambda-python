from aws_lambda_powertools.utilities.parser import envelopes, event_parser
from aws_lambda_powertools.utilities.parser.models import LambdaFunctionUrlModel
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyALambdaFuncUrlBusiness
from tests.functional.utils import load_event


@event_parser(model=MyALambdaFuncUrlBusiness, envelope=envelopes.LambdaFunctionUrlEnvelope)
def handle_lambda_func_url_with_envelope(event: MyALambdaFuncUrlBusiness, _: LambdaContext):
    assert event.message == "Hello"
    assert event.username == "Ran"


@event_parser(model=LambdaFunctionUrlModel)
def handle_lambda_func_url_event(event: LambdaFunctionUrlModel, _: LambdaContext):
    return event


def test_lambda_func_url_event_with_envelope():
    event = load_event("lambdaFunctionUrlEvent.json")
    event["body"] = '{"message": "Hello", "username": "Ran"}'
    handle_lambda_func_url_with_envelope(event, LambdaContext())


def test_lambda_function_url_event():
    json_event = load_event("lambdaFunctionUrlEvent.json")
    event: LambdaFunctionUrlModel = handle_lambda_func_url_event(json_event, LambdaContext())

    assert event.version == "2.0"
    assert event.routeKey == "$default"

    assert event.rawQueryString == ""

    assert event.cookies is None

    headers = event.headers
    assert len(headers) == 20

    assert event.queryStringParameters is None

    assert event.isBase64Encoded is False
    assert event.body is None
    assert event.pathParameters is None
    assert event.stageVariables is None

    request_context = event.requestContext

    assert request_context.accountId == "anonymous"
    assert request_context.apiId is not None
    assert request_context.domainName == "<url-id>.lambda-url.us-east-1.on.aws"
    assert request_context.domainPrefix == "<url-id>"
    assert request_context.requestId == "id"
    assert request_context.routeKey == "$default"
    assert request_context.stage == "$default"
    assert request_context.time is not None
    convert_time = int(round(request_context.timeEpoch.timestamp() * 1000))
    assert convert_time == 1659687279885
    assert request_context.authorizer is None

    http = request_context.http
    assert http.method == "GET"
    assert http.path == "/"
    assert http.protocol == "HTTP/1.1"
    assert str(http.sourceIp) == "123.123.123.123/32"
    assert http.userAgent == "agent"

    assert request_context.authorizer is None


def test_lambda_function_url_event_iam():
    json_event = load_event("lambdaFunctionUrlIAMEvent.json")
    event: LambdaFunctionUrlModel = handle_lambda_func_url_event(json_event, LambdaContext())

    assert event.version == "2.0"
    assert event.routeKey == "$default"

    assert event.rawQueryString == "parameter1=value1&parameter1=value2&parameter2=value"

    cookies = event.cookies
    assert len(cookies) == 2
    assert cookies[0] == "cookie1"

    headers = event.headers
    assert len(headers) == 2

    query_string_parameters = event.queryStringParameters
    assert len(query_string_parameters) == 2
    assert query_string_parameters.get("parameter2") == "value"

    assert event.isBase64Encoded is False
    assert event.body == "Hello from client!"
    assert event.pathParameters is None
    assert event.stageVariables is None

    request_context = event.requestContext

    assert request_context.accountId == "123456789012"
    assert request_context.apiId is not None
    assert request_context.domainName == "<url-id>.lambda-url.us-west-2.on.aws"
    assert request_context.domainPrefix == "<url-id>"
    assert request_context.requestId == "id"
    assert request_context.routeKey == "$default"
    assert request_context.stage == "$default"
    assert request_context.time is not None
    convert_time = int(round(request_context.timeEpoch.timestamp() * 1000))
    assert convert_time == 1583348638390

    http = request_context.http
    assert http.method == "POST"
    assert http.path == "/my/path"
    assert http.protocol == "HTTP/1.1"
    assert str(http.sourceIp) == "123.123.123.123/32"
    assert http.userAgent == "agent"

    authorizer = request_context.authorizer
    assert authorizer is not None
    assert authorizer.jwt is None
    assert authorizer.lambda_value is None

    iam = authorizer.iam
    assert iam is not None
    assert iam.accessKey == "AKIA..."
    assert iam.accountId == "111122223333"
    assert iam.callerId == "AIDA..."
    assert iam.cognitoIdentity is None
    assert iam.principalOrgId is None
    assert iam.userId == "AIDA..."
    assert iam.userArn == "arn:aws:iam::111122223333:user/example-user"
