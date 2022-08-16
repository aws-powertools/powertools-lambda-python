import pytest
from pydantic import ValidationError

from aws_lambda_powertools.utilities.parser import envelopes, event_parser, parse
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyApiGatewayBusiness
from tests.functional.utils import load_event


@event_parser(model=MyApiGatewayBusiness, envelope=envelopes.ApiGatewayEnvelope)
def handle_apigw_with_envelope(event: MyApiGatewayBusiness, _: LambdaContext):
    assert event.message == "Hello"
    assert event.username == "Ran"


@event_parser(model=APIGatewayProxyEventModel)
def handle_apigw_event(event: APIGatewayProxyEventModel, _: LambdaContext):
    assert event.body == "Hello from Lambda!"
    return event


def test_apigw_event_with_envelope():
    event = load_event("apiGatewayProxyEvent.json")
    event["body"] = '{"message": "Hello", "username": "Ran"}'
    handle_apigw_with_envelope(event, LambdaContext())


def test_apigw_event():
    event = load_event("apiGatewayProxyEvent.json")
    parsed_event: APIGatewayProxyEventModel = handle_apigw_event(event, LambdaContext())
    assert parsed_event.version == event["version"]
    assert parsed_event.resource == event["resource"]
    assert parsed_event.path == event["path"]
    assert parsed_event.headers == event["headers"]
    assert parsed_event.multiValueHeaders == event["multiValueHeaders"]
    assert parsed_event.queryStringParameters == event["queryStringParameters"]
    assert parsed_event.multiValueQueryStringParameters == event["multiValueQueryStringParameters"]

    request_context = parsed_event.requestContext
    assert request_context.accountId == event["requestContext"]["accountId"]
    assert request_context.apiId == event["requestContext"]["apiId"]

    authorizer = request_context.authorizer
    assert authorizer.claims is None
    assert authorizer.scopes is None

    assert request_context.domainName == event["requestContext"]["domainName"]
    assert request_context.domainPrefix == event["requestContext"]["domainPrefix"]
    assert request_context.extendedRequestId == event["requestContext"]["extendedRequestId"]
    assert request_context.httpMethod == event["requestContext"]["httpMethod"]

    identity = request_context.identity
    assert identity.accessKey == event["requestContext"]["identity"]["accessKey"]
    assert identity.accountId == event["requestContext"]["identity"]["accountId"]
    assert identity.caller == event["requestContext"]["identity"]["caller"]
    assert (
        identity.cognitoAuthenticationProvider == event["requestContext"]["identity"]["cognitoAuthenticationProvider"]
    )
    assert identity.cognitoAuthenticationType == event["requestContext"]["identity"]["cognitoAuthenticationType"]
    assert identity.cognitoIdentityId == event["requestContext"]["identity"]["cognitoIdentityId"]
    assert identity.cognitoIdentityPoolId == event["requestContext"]["identity"]["cognitoIdentityPoolId"]
    assert identity.principalOrgId == event["requestContext"]["identity"]["principalOrgId"]
    assert str(identity.sourceIp) == event["requestContext"]["identity"]["sourceIp"]
    assert identity.user == event["requestContext"]["identity"]["user"]
    assert identity.userAgent == event["requestContext"]["identity"]["userAgent"]
    assert identity.userArn == event["requestContext"]["identity"]["userArn"]
    assert identity.clientCert is not None
    assert identity.clientCert.clientCertPem == event["requestContext"]["identity"]["clientCert"]["clientCertPem"]
    assert identity.clientCert.subjectDN == event["requestContext"]["identity"]["clientCert"]["subjectDN"]
    assert identity.clientCert.issuerDN == event["requestContext"]["identity"]["clientCert"]["issuerDN"]
    assert identity.clientCert.serialNumber == event["requestContext"]["identity"]["clientCert"]["serialNumber"]
    assert (
        identity.clientCert.validity.notBefore
        == event["requestContext"]["identity"]["clientCert"]["validity"]["notBefore"]
    )
    assert (
        identity.clientCert.validity.notAfter
        == event["requestContext"]["identity"]["clientCert"]["validity"]["notAfter"]
    )

    assert request_context.path == event["requestContext"]["path"]
    assert request_context.protocol == event["requestContext"]["protocol"]
    assert request_context.requestId == event["requestContext"]["requestId"]
    assert request_context.requestTime == event["requestContext"]["requestTime"]
    convert_time = int(round(request_context.requestTimeEpoch.timestamp() * 1000))
    assert convert_time == 1583349317135
    assert request_context.resourceId == event["requestContext"]["resourceId"]
    assert request_context.resourcePath == event["requestContext"]["resourcePath"]
    assert request_context.stage == event["requestContext"]["stage"]

    assert parsed_event.pathParameters == event["pathParameters"]
    assert parsed_event.stageVariables == event["stageVariables"]
    assert parsed_event.body == event["body"]
    assert parsed_event.isBase64Encoded == event["isBase64Encoded"]

    assert request_context.connectedAt is None
    assert request_context.connectionId is None
    assert request_context.eventType is None
    assert request_context.messageDirection is None
    assert request_context.messageId is None
    assert request_context.routeKey is None
    assert request_context.operationName is None
    assert identity.apiKey is None
    assert identity.apiKeyId is None


def test_apigw_event_with_invalid_websocket_request():
    # GIVEN an event with an eventType != MESSAGE and has  a messageId
    event = {
        "resource": "/",
        "path": "/",
        "httpMethod": "GET",
        "headers": {},
        "multiValueHeaders": {},
        "isBase64Encoded": False,
        "body": "Foo!",
        "requestContext": {
            "accountId": "1234",
            "apiId": "myApi",
            "httpMethod": "GET",
            "identity": {
                "sourceIp": "127.0.0.1",
            },
            "path": "/",
            "protocol": "Https",
            "requestId": "1234",
            "requestTime": "2018-09-07T16:20:46Z",
            "requestTimeEpoch": 1536992496000,
            "resourcePath": "/",
            "stage": "test",
            "eventType": "DISCONNECT",
            "messageId": "messageId",
        },
    }

    # WHEN calling event_parser with APIGatewayProxyEventModel
    with pytest.raises(ValidationError) as err:
        handle_apigw_event(event, LambdaContext())

    # THEN raise TypeError for invalid event
    errors = err.value.errors()
    assert len(errors) == 1
    expected_msg = "messageId is available only when the `eventType` is `MESSAGE`"
    assert errors[0]["msg"] == expected_msg
    assert expected_msg in str(err.value)


def test_apigw_event_empty_body():
    event = load_event("apiGatewayProxyEvent.json")
    event["body"] = None
    parse(event=event, model=APIGatewayProxyEventModel)
