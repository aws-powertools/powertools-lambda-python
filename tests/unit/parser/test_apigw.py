import pytest
from pydantic import ValidationError

from aws_lambda_powertools.utilities.parser import envelopes, parse
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from tests.functional.utils import load_event
from tests.unit.parser.schemas import MyApiGatewayBusiness


def test_apigw_event_with_envelope():
    raw_event = load_event("apiGatewayProxyEvent.json")
    raw_event["body"] = '{"message": "Hello", "username": "Ran"}'
    parsed_event: MyApiGatewayBusiness = parse(
        event=raw_event,
        model=MyApiGatewayBusiness,
        envelope=envelopes.ApiGatewayEnvelope,
    )

    assert parsed_event.message == "Hello"
    assert parsed_event.username == "Ran"


def test_apigw_event():
    raw_event = load_event("apiGatewayProxyEvent.json")
    parsed_event: APIGatewayProxyEventModel = APIGatewayProxyEventModel(**raw_event)

    assert parsed_event.version == raw_event["version"]
    assert parsed_event.resource == raw_event["resource"]
    assert parsed_event.path == raw_event["path"]
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.multiValueHeaders == raw_event["multiValueHeaders"]
    assert parsed_event.queryStringParameters == raw_event["queryStringParameters"]
    assert parsed_event.multiValueQueryStringParameters == raw_event["multiValueQueryStringParameters"]

    request_context = parsed_event.requestContext
    assert request_context.accountId == raw_event["requestContext"]["accountId"]
    assert request_context.apiId == raw_event["requestContext"]["apiId"]

    authorizer = request_context.authorizer
    assert authorizer.claims is None
    assert authorizer.scopes is None

    assert request_context.domainName == raw_event["requestContext"]["domainName"]
    assert request_context.domainPrefix == raw_event["requestContext"]["domainPrefix"]
    assert request_context.extendedRequestId == raw_event["requestContext"]["extendedRequestId"]
    assert request_context.httpMethod == raw_event["requestContext"]["httpMethod"]

    identity = request_context.identity
    assert identity.accessKey == raw_event["requestContext"]["identity"]["accessKey"]
    assert identity.accountId == raw_event["requestContext"]["identity"]["accountId"]
    assert identity.caller == raw_event["requestContext"]["identity"]["caller"]
    assert (
        identity.cognitoAuthenticationProvider
        == raw_event["requestContext"]["identity"]["cognitoAuthenticationProvider"]
    )
    assert identity.cognitoAuthenticationType == raw_event["requestContext"]["identity"]["cognitoAuthenticationType"]
    assert identity.cognitoIdentityId == raw_event["requestContext"]["identity"]["cognitoIdentityId"]
    assert identity.cognitoIdentityPoolId == raw_event["requestContext"]["identity"]["cognitoIdentityPoolId"]
    assert identity.principalOrgId == raw_event["requestContext"]["identity"]["principalOrgId"]
    assert str(identity.sourceIp) == raw_event["requestContext"]["identity"]["sourceIp"]
    assert identity.user == raw_event["requestContext"]["identity"]["user"]
    assert identity.userAgent == raw_event["requestContext"]["identity"]["userAgent"]
    assert identity.userArn == raw_event["requestContext"]["identity"]["userArn"]
    assert identity.clientCert is not None
    assert identity.clientCert.clientCertPem == raw_event["requestContext"]["identity"]["clientCert"]["clientCertPem"]
    assert identity.clientCert.subjectDN == raw_event["requestContext"]["identity"]["clientCert"]["subjectDN"]
    assert identity.clientCert.issuerDN == raw_event["requestContext"]["identity"]["clientCert"]["issuerDN"]
    assert identity.clientCert.serialNumber == raw_event["requestContext"]["identity"]["clientCert"]["serialNumber"]
    assert (
        identity.clientCert.validity.notBefore
        == raw_event["requestContext"]["identity"]["clientCert"]["validity"]["notBefore"]
    )
    assert (
        identity.clientCert.validity.notAfter
        == raw_event["requestContext"]["identity"]["clientCert"]["validity"]["notAfter"]
    )

    assert request_context.path == raw_event["requestContext"]["path"]
    assert request_context.protocol == raw_event["requestContext"]["protocol"]
    assert request_context.requestId == raw_event["requestContext"]["requestId"]
    assert request_context.requestTime == raw_event["requestContext"]["requestTime"]
    convert_time = int(round(request_context.requestTimeEpoch.timestamp() * 1000))
    assert convert_time == 1583349317135
    assert request_context.resourceId == raw_event["requestContext"]["resourceId"]
    assert request_context.resourcePath == raw_event["requestContext"]["resourcePath"]
    assert request_context.stage == raw_event["requestContext"]["stage"]

    assert parsed_event.pathParameters == raw_event["pathParameters"]
    assert parsed_event.stageVariables == raw_event["stageVariables"]
    assert parsed_event.body == raw_event["body"]
    assert parsed_event.isBase64Encoded == raw_event["isBase64Encoded"]

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
        APIGatewayProxyEventModel(**event)

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
