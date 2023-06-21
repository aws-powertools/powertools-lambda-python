from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    APIGatewayAuthorizerEventV2,
    APIGatewayAuthorizerRequestEvent,
    APIGatewayAuthorizerResponseV2,
    APIGatewayAuthorizerTokenEvent,
)
from tests.functional.utils import load_event


def test_api_gateway_authorizer_v2():
    """Check api gateway authorize event format v2.0"""
    raw_event = load_event("apiGatewayAuthorizerV2Event.json")
    parsed_event = APIGatewayAuthorizerEventV2(raw_event)

    assert parsed_event.version == raw_event["version"]
    assert parsed_event.get_type == raw_event["type"]
    assert parsed_event.route_arn == raw_event["routeArn"]
    assert parsed_event.route_arn == "arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/request"
    assert parsed_event.identity_source == raw_event["identitySource"]
    assert parsed_event.route_key == raw_event["routeKey"]
    assert parsed_event.raw_path == raw_event["rawPath"]
    assert parsed_event.raw_query_string == raw_event["rawQueryString"]
    assert parsed_event.cookies == raw_event["cookies"]
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.query_string_parameters == raw_event["queryStringParameters"]
    assert parsed_event.request_context.account_id == raw_event["requestContext"]["accountId"]
    assert parsed_event.request_context.api_id == raw_event["requestContext"]["apiId"]
    expected_client_cert = raw_event["requestContext"]["authentication"]["clientCert"]
    assert parsed_event.request_context.authentication.client_cert_pem == expected_client_cert["clientCertPem"]
    assert parsed_event.request_context.authentication.subject_dn == expected_client_cert["subjectDN"]
    assert parsed_event.request_context.authentication.issuer_dn == expected_client_cert["issuerDN"]
    assert parsed_event.request_context.authentication.serial_number == expected_client_cert["serialNumber"]
    assert (
        parsed_event.request_context.authentication.validity_not_after == expected_client_cert["validity"]["notAfter"]
    )
    assert (
        parsed_event.request_context.authentication.validity_not_before == expected_client_cert["validity"]["notBefore"]
    )
    assert parsed_event.request_context.domain_name == raw_event["requestContext"]["domainName"]
    assert parsed_event.request_context.domain_prefix == raw_event["requestContext"]["domainPrefix"]
    expected_http = raw_event["requestContext"]["http"]
    assert parsed_event.request_context.http.method == expected_http["method"]
    assert parsed_event.request_context.http.path == expected_http["path"]
    assert parsed_event.request_context.http.protocol == expected_http["protocol"]
    assert parsed_event.request_context.http.source_ip == expected_http["sourceIp"]
    assert parsed_event.request_context.http.user_agent == expected_http["userAgent"]
    assert parsed_event.request_context.request_id == raw_event["requestContext"]["requestId"]
    assert parsed_event.request_context.route_key == raw_event["requestContext"]["routeKey"]
    assert parsed_event.request_context.stage == raw_event["requestContext"]["stage"]
    assert parsed_event.request_context.time == raw_event["requestContext"]["time"]
    assert parsed_event.request_context.time_epoch == raw_event["requestContext"]["timeEpoch"]
    assert parsed_event.path_parameters == raw_event["pathParameters"]
    assert parsed_event.stage_variables == raw_event["stageVariables"]

    assert parsed_event.get_header_value("Authorization") == "value"
    assert parsed_event.get_header_value("authorization") == "value"
    assert parsed_event.get_header_value("missing") is None

    # Check for optionals
    event_optionals = APIGatewayAuthorizerEventV2({"requestContext": {}})
    assert event_optionals.identity_source is None
    assert event_optionals.request_context.authentication is None
    assert event_optionals.path_parameters is None
    assert event_optionals.stage_variables is None


def test_api_gateway_authorizer_token_event():
    """Check API Gateway authorizer token event"""
    raw_event = load_event("apiGatewayAuthorizerTokenEvent.json")
    parsed_event = APIGatewayAuthorizerTokenEvent(raw_event)

    assert parsed_event.authorization_token == raw_event["authorizationToken"]
    assert parsed_event.method_arn == raw_event["methodArn"]
    assert parsed_event.parsed_arn.arn == "arn:aws:execute-api:us-west-2:123456789012:ymy8tbxw7b/*/GET/"
    assert parsed_event.get_type == raw_event["type"]


def test_api_gateway_authorizer_request_event():
    """Check API Gateway authorizer token event"""
    raw_event = load_event("apiGatewayAuthorizerRequestEvent.json")
    parsed_event = APIGatewayAuthorizerRequestEvent(raw_event)

    assert parsed_event.version == raw_event["version"]
    assert parsed_event.get_type == raw_event["type"]
    assert parsed_event.method_arn == raw_event["methodArn"]
    assert parsed_event.parsed_arn.arn == "arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/request"
    assert parsed_event.identity_source == raw_event["identitySource"]
    assert parsed_event.authorization_token == raw_event["authorizationToken"]
    assert parsed_event.resource == raw_event["resource"]
    assert parsed_event.path == raw_event["path"]
    assert parsed_event.http_method == raw_event["httpMethod"]
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.get_header_value("accept") == "*/*"
    assert parsed_event.query_string_parameters == raw_event["queryStringParameters"]
    assert parsed_event.path_parameters == raw_event["pathParameters"]
    assert parsed_event.stage_variables == raw_event["stageVariables"]

    assert parsed_event.request_context is not None
    request_context = parsed_event.request_context
    request_context_raw = raw_event["requestContext"]
    assert request_context.account_id == request_context_raw["accountId"]
    assert request_context.api_id == request_context_raw["apiId"]
    assert request_context.domain_name == request_context_raw["domainName"]
    assert request_context.domain_prefix == request_context_raw["domainPrefix"]
    assert request_context.extended_request_id == request_context_raw["extendedRequestId"]
    assert request_context.http_method == request_context_raw["httpMethod"]
    assert request_context.path == request_context_raw["path"]
    assert request_context.protocol == request_context_raw["protocol"]
    assert request_context.request_id == request_context_raw["requestId"]
    assert request_context.request_time == request_context_raw["requestTime"]
    assert request_context.request_time_epoch == request_context_raw["requestTimeEpoch"]
    assert request_context.resource_id == request_context_raw["resourceId"]
    assert request_context.resource_path == request_context_raw["resourcePath"]
    assert request_context.stage == request_context_raw["stage"]

    identity = request_context.identity
    identity_raw = raw_event["requestContext"]["identity"]
    assert identity.access_key == identity_raw["accessKey"]
    assert identity.account_id == identity_raw["accountId"]
    assert identity.caller == identity_raw["caller"]
    assert identity.cognito_authentication_provider == identity_raw["cognitoAuthenticationProvider"]
    assert identity.cognito_authentication_type == identity_raw["cognitoAuthenticationType"]
    assert identity.cognito_identity_id == identity_raw["cognitoIdentityId"]
    assert identity.cognito_identity_pool_id == identity_raw["cognitoIdentityPoolId"]
    assert identity.principal_org_id == identity_raw["principalOrgId"]
    assert identity.source_ip == identity_raw["sourceIp"]
    assert identity.user == identity_raw["user"]
    assert identity.user_agent == identity_raw["userAgent"]
    assert identity.user_arn == identity_raw["userArn"]
    assert identity.client_cert.subject_dn == "www.example.com"


def test_api_gateway_authorizer_simple_response():
    """Check building API Gateway authorizer simple resource"""
    assert {"isAuthorized": False} == APIGatewayAuthorizerResponseV2().asdict()
    expected_context = {"foo": "value"}
    assert {"isAuthorized": True, "context": expected_context} == APIGatewayAuthorizerResponseV2(
        authorize=True,
        context=expected_context,
    ).asdict()
