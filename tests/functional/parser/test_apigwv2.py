from aws_lambda_powertools.utilities.parser import envelopes, event_parser, parse
from aws_lambda_powertools.utilities.parser.models import (
    APIGatewayProxyEventV2Model,
    RequestContextV2,
    RequestContextV2Authorizer,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyApiGatewayBusiness
from tests.functional.utils import load_event


@event_parser(model=MyApiGatewayBusiness, envelope=envelopes.ApiGatewayV2Envelope)
def handle_apigw_with_envelope(event: MyApiGatewayBusiness, _: LambdaContext):
    assert event.message == "Hello"
    assert event.username == "Ran"


@event_parser(model=APIGatewayProxyEventV2Model)
def handle_apigw_event(event: APIGatewayProxyEventV2Model, _: LambdaContext):
    return event


def test_apigw_v2_event_with_envelope():
    event = load_event("apiGatewayProxyV2Event.json")
    event["body"] = '{"message": "Hello", "username": "Ran"}'
    handle_apigw_with_envelope(event, LambdaContext())


def test_apigw_v2_event_jwt_authorizer():
    event = load_event("apiGatewayProxyV2Event.json")
    parsed_event: APIGatewayProxyEventV2Model = handle_apigw_event(event, LambdaContext())
    assert parsed_event.version == event["version"]
    assert parsed_event.routeKey == event["routeKey"]
    assert parsed_event.rawPath == event["rawPath"]
    assert parsed_event.rawQueryString == event["rawQueryString"]
    assert parsed_event.cookies == event["cookies"]
    assert parsed_event.cookies[0] == "cookie1"
    assert parsed_event.headers == event["headers"]
    assert parsed_event.queryStringParameters == event["queryStringParameters"]
    assert parsed_event.queryStringParameters["parameter2"] == "value"

    request_context = parsed_event.requestContext
    assert request_context.accountId == event["requestContext"]["accountId"]
    assert request_context.apiId == event["requestContext"]["apiId"]
    assert request_context.authorizer.jwt.claims == event["requestContext"]["authorizer"]["jwt"]["claims"]
    assert request_context.authorizer.jwt.scopes == event["requestContext"]["authorizer"]["jwt"]["scopes"]
    assert request_context.domainName == event["requestContext"]["domainName"]
    assert request_context.domainPrefix == event["requestContext"]["domainPrefix"]

    http = request_context.http
    assert http.method == "POST"
    assert http.path == "/my/path"
    assert http.protocol == "HTTP/1.1"
    assert str(http.sourceIp) == "192.168.0.1/32"
    assert http.userAgent == "agent"

    assert request_context.requestId == event["requestContext"]["requestId"]
    assert request_context.routeKey == event["requestContext"]["routeKey"]
    assert request_context.stage == event["requestContext"]["stage"]
    assert request_context.time == event["requestContext"]["time"]
    convert_time = int(round(request_context.timeEpoch.timestamp() * 1000))
    assert convert_time == event["requestContext"]["timeEpoch"]
    assert parsed_event.body == event["body"]
    assert parsed_event.pathParameters == event["pathParameters"]
    assert parsed_event.isBase64Encoded == event["isBase64Encoded"]
    assert parsed_event.stageVariables == event["stageVariables"]


def test_api_gateway_proxy_v2_event_lambda_authorizer():
    event = load_event("apiGatewayProxyV2LambdaAuthorizerEvent.json")
    parsed_event: APIGatewayProxyEventV2Model = handle_apigw_event(event, LambdaContext())
    request_context: RequestContextV2 = parsed_event.requestContext
    assert request_context is not None
    lambda_props: RequestContextV2Authorizer = request_context.authorizer.lambda_value
    assert lambda_props is not None
    assert lambda_props["key"] == "value"


def test_api_gateway_proxy_v2_event_iam_authorizer():
    event = load_event("apiGatewayProxyV2IamEvent.json")
    parsed_event: APIGatewayProxyEventV2Model = handle_apigw_event(event, LambdaContext())
    iam = parsed_event.requestContext.authorizer.iam
    assert iam is not None
    assert iam.accessKey == "ARIA2ZJZYVUEREEIHAKY"
    assert iam.accountId == "1234567890"
    assert iam.callerId == "AROA7ZJZYVRE7C3DUXHH6:CognitoIdentityCredentials"
    assert iam.cognitoIdentity.amr == ["foo"]
    assert iam.cognitoIdentity.identityId == "us-east-1:3f291106-8703-466b-8f2b-3ecee1ca56ce"
    assert iam.cognitoIdentity.identityPoolId == "us-east-1:4f291106-8703-466b-8f2b-3ecee1ca56ce"
    assert iam.principalOrgId == "AwsOrgId"
    assert iam.userArn == "arn:aws:iam::1234567890:user/Admin"
    assert iam.userId == "AROA2ZJZYVRE7Y3TUXHH6"


def test_apigw_event_empty_body():
    event = load_event("apiGatewayProxyV2Event.json")
    event.pop("body")  # API GW v2 removes certain keys when no data is passed
    parse(event=event, model=APIGatewayProxyEventV2Model)


def test_apigw_event_empty_query_strings():
    event = load_event("apiGatewayProxyV2Event.json")
    event["rawQueryString"] = ""
    event.pop("queryStringParameters")  # API GW v2 removes certain keys when no data is passed
    parse(event=event, model=APIGatewayProxyEventV2Model)
