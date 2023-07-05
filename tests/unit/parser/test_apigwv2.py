from aws_lambda_powertools.utilities.parser import envelopes, parse
from aws_lambda_powertools.utilities.parser.models import (
    APIGatewayProxyEventV2Model,
    RequestContextV2,
    RequestContextV2Authorizer,
)
from tests.functional.utils import load_event
from tests.unit.parser.schemas import MyApiGatewayBusiness


def test_apigw_v2_event_with_envelope():
    raw_event = load_event("apiGatewayProxyV2Event.json")
    raw_event["body"] = '{"message": "Hello", "username": "Ran"}'
    parsed_event: MyApiGatewayBusiness = parse(
        event=raw_event,
        model=MyApiGatewayBusiness,
        envelope=envelopes.ApiGatewayV2Envelope,
    )

    assert parsed_event.message == "Hello"
    assert parsed_event.username == "Ran"


def test_apigw_v2_event_jwt_authorizer():
    raw_event = load_event("apiGatewayProxyV2Event.json")
    parsed_event: APIGatewayProxyEventV2Model = APIGatewayProxyEventV2Model(**raw_event)

    assert parsed_event.version == raw_event["version"]
    assert parsed_event.routeKey == raw_event["routeKey"]
    assert parsed_event.rawPath == raw_event["rawPath"]
    assert parsed_event.rawQueryString == raw_event["rawQueryString"]
    assert parsed_event.cookies == raw_event["cookies"]
    assert parsed_event.cookies[0] == "cookie1"
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.queryStringParameters == raw_event["queryStringParameters"]
    assert parsed_event.queryStringParameters.get("parameter2") == raw_event["queryStringParameters"]["parameter2"]

    request_context = parsed_event.requestContext
    assert request_context.accountId == raw_event["requestContext"]["accountId"]
    assert request_context.apiId == raw_event["requestContext"]["apiId"]
    assert request_context.authorizer.jwt.claims == raw_event["requestContext"]["authorizer"]["jwt"]["claims"]
    assert request_context.authorizer.jwt.scopes == raw_event["requestContext"]["authorizer"]["jwt"]["scopes"]
    assert request_context.domainName == raw_event["requestContext"]["domainName"]
    assert request_context.domainPrefix == raw_event["requestContext"]["domainPrefix"]

    http = request_context.http
    raw_http = raw_event["requestContext"]["http"]
    assert http.method == raw_http["method"]
    assert http.path == raw_http["path"]
    assert http.protocol == raw_http["protocol"]
    assert str(http.sourceIp) == raw_http["sourceIp"]
    assert http.userAgent == raw_http["userAgent"]

    assert request_context.requestId == raw_event["requestContext"]["requestId"]
    assert request_context.routeKey == raw_event["requestContext"]["routeKey"]
    assert request_context.stage == raw_event["requestContext"]["stage"]
    assert request_context.time == raw_event["requestContext"]["time"]
    convert_time = int(round(request_context.timeEpoch.timestamp() * 1000))
    assert convert_time == raw_event["requestContext"]["timeEpoch"]
    assert parsed_event.body == raw_event["body"]
    assert parsed_event.pathParameters == raw_event["pathParameters"]
    assert parsed_event.isBase64Encoded == raw_event["isBase64Encoded"]
    assert parsed_event.stageVariables == raw_event["stageVariables"]


def test_api_gateway_proxy_v2_event_lambda_authorizer():
    raw_event = load_event("apiGatewayProxyV2LambdaAuthorizerEvent.json")
    parsed_event: APIGatewayProxyEventV2Model = APIGatewayProxyEventV2Model(**raw_event)

    request_context: RequestContextV2 = parsed_event.requestContext
    assert request_context is not None

    lambda_props: RequestContextV2Authorizer = request_context.authorizer.lambda_value
    assert lambda_props is not None
    assert lambda_props["key"] == raw_event["requestContext"]["authorizer"]["lambda"]["key"]


def test_api_gateway_proxy_v2_event_iam_authorizer():
    raw_event = load_event("apiGatewayProxyV2IamEvent.json")
    parsed_event: APIGatewayProxyEventV2Model = APIGatewayProxyEventV2Model(**raw_event)

    iam = parsed_event.requestContext.authorizer.iam
    raw_iam = raw_event["requestContext"]["authorizer"]["iam"]
    assert iam is not None
    assert iam.accessKey == raw_iam["accessKey"]
    assert iam.accountId == raw_iam["accountId"]
    assert iam.callerId == raw_iam["callerId"]
    assert iam.cognitoIdentity.amr == raw_iam["cognitoIdentity"]["amr"]
    assert iam.cognitoIdentity.identityId == raw_iam["cognitoIdentity"]["identityId"]
    assert iam.cognitoIdentity.identityPoolId == raw_iam["cognitoIdentity"]["identityPoolId"]
    assert iam.principalOrgId == raw_iam["principalOrgId"]
    assert iam.userArn == raw_iam["userArn"]
    assert iam.userId == raw_iam["userId"]


def test_apigw_event_empty_body():
    raw_event = load_event("apiGatewayProxyV2Event.json")
    raw_event.pop("body")  # API GW v2 removes certain keys when no data is passed
    parse(event=raw_event, model=APIGatewayProxyEventV2Model)


def test_apigw_event_empty_query_strings():
    raw_event = load_event("apiGatewayProxyV2Event.json")
    raw_event["rawQueryString"] = ""
    raw_event.pop("queryStringParameters")  # API GW v2 removes certain keys when no data is passed
    parse(event=raw_event, model=APIGatewayProxyEventV2Model)
