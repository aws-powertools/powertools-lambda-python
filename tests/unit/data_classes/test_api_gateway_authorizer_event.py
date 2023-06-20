from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    APIGatewayAuthorizerEventV2,
    APIGatewayAuthorizerRequestEvent,
    APIGatewayAuthorizerResponseV2,
    APIGatewayAuthorizerTokenEvent,
)
from tests.functional.utils import load_event


def test_api_gateway_authorizer_v2():
    """Check api gateway authorize event format v2.0"""
    event = APIGatewayAuthorizerEventV2(load_event("apiGatewayAuthorizerV2Event.json"))

    assert event["version"] == event.version
    assert event["version"] == "2.0"
    assert event["type"] == event.get_type
    assert event["routeArn"] == event.route_arn
    assert event.parsed_arn.arn == event.route_arn
    assert event["identitySource"] == event.identity_source
    assert event["routeKey"] == event.route_key
    assert event["rawPath"] == event.raw_path
    assert event["rawQueryString"] == event.raw_query_string
    assert event["cookies"] == event.cookies
    assert event["headers"] == event.headers
    assert event["queryStringParameters"] == event.query_string_parameters
    assert event["requestContext"]["accountId"] == event.request_context.account_id
    assert event["requestContext"]["apiId"] == event.request_context.api_id
    expected_client_cert = event["requestContext"]["authentication"]["clientCert"]
    assert expected_client_cert["clientCertPem"] == event.request_context.authentication.client_cert_pem
    assert expected_client_cert["subjectDN"] == event.request_context.authentication.subject_dn
    assert expected_client_cert["issuerDN"] == event.request_context.authentication.issuer_dn
    assert expected_client_cert["serialNumber"] == event.request_context.authentication.serial_number
    assert expected_client_cert["validity"]["notAfter"] == event.request_context.authentication.validity_not_after
    assert expected_client_cert["validity"]["notBefore"] == event.request_context.authentication.validity_not_before
    assert event["requestContext"]["domainName"] == event.request_context.domain_name
    assert event["requestContext"]["domainPrefix"] == event.request_context.domain_prefix
    expected_http = event["requestContext"]["http"]
    assert expected_http["method"] == event.request_context.http.method
    assert expected_http["path"] == event.request_context.http.path
    assert expected_http["protocol"] == event.request_context.http.protocol
    assert expected_http["sourceIp"] == event.request_context.http.source_ip
    assert expected_http["userAgent"] == event.request_context.http.user_agent
    assert event["requestContext"]["requestId"] == event.request_context.request_id
    assert event["requestContext"]["routeKey"] == event.request_context.route_key
    assert event["requestContext"]["stage"] == event.request_context.stage
    assert event["requestContext"]["time"] == event.request_context.time
    assert event["requestContext"]["timeEpoch"] == event.request_context.time_epoch
    assert event["pathParameters"] == event.path_parameters
    assert event["stageVariables"] == event.stage_variables

    assert event.get_header_value("Authorization") == "value"
    assert event.get_header_value("authorization") == "value"
    assert event.get_header_value("missing") is None

    # Check for optionals
    event_optionals = APIGatewayAuthorizerEventV2({"requestContext": {}})
    assert event_optionals.identity_source is None
    assert event_optionals.request_context.authentication is None
    assert event_optionals.path_parameters is None
    assert event_optionals.stage_variables is None


def test_api_gateway_authorizer_token_event():
    """Check API Gateway authorizer token event"""
    event = APIGatewayAuthorizerTokenEvent(load_event("apiGatewayAuthorizerTokenEvent.json"))

    assert event.authorization_token == event["authorizationToken"]
    assert event.method_arn == event["methodArn"]
    assert event.parsed_arn.arn == event.method_arn
    assert event.get_type == event["type"]


def test_api_gateway_authorizer_request_event():
    """Check API Gateway authorizer token event"""
    event = APIGatewayAuthorizerRequestEvent(load_event("apiGatewayAuthorizerRequestEvent.json"))

    assert event.version == event["version"]
    assert event.get_type == event["type"]
    assert event.method_arn == event["methodArn"]
    assert event.parsed_arn.arn == event.method_arn
    assert event.identity_source == event["identitySource"]
    assert event.authorization_token == event["authorizationToken"]
    assert event.resource == event["resource"]
    assert event.path == event["path"]
    assert event.http_method == event["httpMethod"]
    assert event.headers == event["headers"]
    assert event.get_header_value("accept") == "*/*"
    assert event.query_string_parameters == event["queryStringParameters"]
    assert event.path_parameters == event["pathParameters"]
    assert event.stage_variables == event["stageVariables"]

    assert event.request_context is not None
    request_context = event.request_context
    assert request_context.account_id == event["requestContext"]["accountId"]
    assert request_context.api_id == event["requestContext"]["apiId"]

    assert request_context.domain_name == event["requestContext"]["domainName"]
    assert request_context.domain_prefix == event["requestContext"]["domainPrefix"]
    assert request_context.extended_request_id == event["requestContext"]["extendedRequestId"]
    assert request_context.http_method == event["requestContext"]["httpMethod"]

    identity = request_context.identity
    assert identity.access_key == event["requestContext"]["identity"]["accessKey"]
    assert identity.account_id == event["requestContext"]["identity"]["accountId"]
    assert identity.caller == event["requestContext"]["identity"]["caller"]
    assert (
        identity.cognito_authentication_provider == event["requestContext"]["identity"]["cognitoAuthenticationProvider"]
    )
    assert identity.cognito_authentication_type == event["requestContext"]["identity"]["cognitoAuthenticationType"]
    assert identity.cognito_identity_id == event["requestContext"]["identity"]["cognitoIdentityId"]
    assert identity.cognito_identity_pool_id == event["requestContext"]["identity"]["cognitoIdentityPoolId"]
    assert identity.principal_org_id == event["requestContext"]["identity"]["principalOrgId"]
    assert identity.source_ip == event["requestContext"]["identity"]["sourceIp"]
    assert identity.user == event["requestContext"]["identity"]["user"]
    assert identity.user_agent == event["requestContext"]["identity"]["userAgent"]
    assert identity.user_arn == event["requestContext"]["identity"]["userArn"]
    assert identity.client_cert.subject_dn == "www.example.com"

    assert request_context.path == event["requestContext"]["path"]
    assert request_context.protocol == event["requestContext"]["protocol"]
    assert request_context.request_id == event["requestContext"]["requestId"]
    assert request_context.request_time == event["requestContext"]["requestTime"]
    assert request_context.request_time_epoch == event["requestContext"]["requestTimeEpoch"]
    assert request_context.resource_id == event["requestContext"]["resourceId"]
    assert request_context.resource_path == event["requestContext"]["resourcePath"]
    assert request_context.stage == event["requestContext"]["stage"]


def test_api_gateway_authorizer_simple_response():
    """Check building API Gateway authorizer simple resource"""
    assert {"isAuthorized": False} == APIGatewayAuthorizerResponseV2().asdict()
    expected_context = {"foo": "value"}
    assert {"isAuthorized": True, "context": expected_context} == APIGatewayAuthorizerResponseV2(
        authorize=True,
        context=expected_context,
    ).asdict()
