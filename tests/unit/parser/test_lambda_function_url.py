from aws_lambda_powertools.utilities.parser import envelopes, parse
from aws_lambda_powertools.utilities.parser.models import LambdaFunctionUrlModel
from tests.functional.utils import load_event
from tests.unit.parser.schemas import MyALambdaFuncUrlBusiness


def test_lambda_func_url_event_with_envelope():
    raw_event = load_event("lambdaFunctionUrlEvent.json")
    raw_event["body"] = '{"message": "Hello", "username": "Ran"}'

    parsed_event: MyALambdaFuncUrlBusiness = parse(
        event=raw_event,
        model=MyALambdaFuncUrlBusiness,
        envelope=envelopes.LambdaFunctionUrlEnvelope,
    )

    assert parsed_event.message == "Hello"
    assert parsed_event.username == "Ran"


def test_lambda_function_url_event():
    raw_event = load_event("lambdaFunctionUrlEvent.json")
    parsed_event: LambdaFunctionUrlModel = LambdaFunctionUrlModel(**raw_event)

    assert parsed_event.version == raw_event["version"]
    assert parsed_event.routeKey == raw_event["routeKey"]

    assert parsed_event.rawQueryString == raw_event["rawQueryString"]

    assert parsed_event.cookies is None

    headers = parsed_event.headers
    assert len(headers) == 20

    assert parsed_event.queryStringParameters is None

    assert parsed_event.isBase64Encoded is False
    assert parsed_event.body is None
    assert parsed_event.pathParameters is None
    assert parsed_event.stageVariables is None

    request_context = parsed_event.requestContext
    raw_request_context = raw_event["requestContext"]

    assert request_context.accountId == raw_request_context["accountId"]
    assert request_context.apiId == raw_request_context["apiId"]
    assert request_context.domainName == raw_request_context["domainName"]
    assert request_context.domainPrefix == raw_request_context["domainPrefix"]
    assert request_context.requestId == raw_request_context["requestId"]
    assert request_context.routeKey == raw_request_context["routeKey"]
    assert request_context.stage == raw_request_context["stage"]
    assert request_context.time == raw_request_context["time"]
    convert_time = int(round(request_context.timeEpoch.timestamp() * 1000))
    assert convert_time == raw_request_context["timeEpoch"]
    assert request_context.authorizer is None

    http = request_context.http
    assert http.method == raw_request_context["http"]["method"]
    assert http.path == raw_request_context["http"]["path"]
    assert http.protocol == raw_request_context["http"]["protocol"]
    assert str(http.sourceIp) == "123.123.123.123/32"
    assert http.userAgent == raw_request_context["http"]["userAgent"]

    assert request_context.authorizer is None


def test_lambda_function_url_event_iam():
    raw_event = load_event("lambdaFunctionUrlIAMEvent.json")
    parsed_event: LambdaFunctionUrlModel = LambdaFunctionUrlModel(**raw_event)

    assert parsed_event.version == raw_event["version"]
    assert parsed_event.routeKey == raw_event["routeKey"]

    assert parsed_event.rawQueryString == raw_event["rawQueryString"]

    cookies = parsed_event.cookies
    assert len(cookies) == 2
    assert cookies[0] == raw_event["cookies"][0]

    headers = parsed_event.headers
    assert len(headers) == 2

    query_string_parameters = parsed_event.queryStringParameters
    assert len(query_string_parameters) == 2
    assert query_string_parameters.get("parameter2") == raw_event["queryStringParameters"]["parameter2"]

    assert parsed_event.isBase64Encoded is False
    assert parsed_event.body == raw_event["body"]
    assert parsed_event.pathParameters is None
    assert parsed_event.stageVariables is None

    request_context = parsed_event.requestContext
    raw_request_context = raw_event["requestContext"]
    assert request_context.accountId == raw_request_context["accountId"]
    assert request_context.apiId == raw_request_context["apiId"]
    assert request_context.domainName == raw_request_context["domainName"]
    assert request_context.domainPrefix == raw_request_context["domainPrefix"]
    assert request_context.requestId == raw_request_context["requestId"]
    assert request_context.routeKey == raw_request_context["routeKey"]
    assert request_context.stage == raw_request_context["stage"]
    assert request_context.time == raw_request_context["time"]
    convert_time = int(round(request_context.timeEpoch.timestamp() * 1000))
    assert convert_time == raw_request_context["timeEpoch"]
    assert request_context.authorizer is not None

    http = request_context.http
    assert http.method == raw_request_context["http"]["method"]
    assert http.path == raw_request_context["http"]["path"]
    assert http.protocol == raw_request_context["http"]["protocol"]
    assert str(http.sourceIp) == "123.123.123.123/32"
    assert http.userAgent == raw_request_context["http"]["userAgent"]

    authorizer = request_context.authorizer
    assert authorizer is not None
    assert authorizer.jwt is None
    assert authorizer.lambda_value is None

    iam = authorizer.iam
    iam_raw = raw_event["requestContext"]["authorizer"]["iam"]
    assert iam is not None
    assert iam.accessKey == iam_raw["accessKey"]
    assert iam.accountId == iam_raw["accountId"]
    assert iam.callerId == iam_raw["callerId"]
    assert iam.cognitoIdentity is None
    assert iam.principalOrgId is None
    assert iam.userId == iam_raw["userId"]
    assert iam.userArn == iam_raw["userArn"]
