from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
    APIGatewayProxyEventV2,
)
from tests.functional.utils import load_event


def test_default_api_gateway_proxy_event():
    event = APIGatewayProxyEvent(load_event("apiGatewayProxyEvent_noVersionAuth.json"))

    assert event.get("version") is None
    assert event.resource == event["resource"]
    assert event.path == event["path"]
    assert event.http_method == event["httpMethod"]
    assert event.headers == event["headers"]
    assert event.multi_value_headers == event["multiValueHeaders"]
    assert event.query_string_parameters == event["queryStringParameters"]
    assert event.multi_value_query_string_parameters == event["multiValueQueryStringParameters"]

    request_context = event.request_context
    assert request_context.account_id == event["requestContext"]["accountId"]
    assert request_context.api_id == event["requestContext"]["apiId"]

    assert request_context.get("authorizer") is None

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

    assert event.path_parameters == event["pathParameters"]
    assert event.stage_variables == event["stageVariables"]
    assert event.body == event["body"]
    assert event.is_base64_encoded == event["isBase64Encoded"]

    assert request_context.connected_at is None
    assert request_context.connection_id is None
    assert request_context.event_type is None
    assert request_context.message_direction is None
    assert request_context.message_id is None
    assert request_context.route_key is None
    assert request_context.operation_name is None
    assert identity.api_key is None
    assert identity.api_key_id is None


def test_api_gateway_proxy_event():
    event = APIGatewayProxyEvent(load_event("apiGatewayProxyEvent.json"))

    assert event.version == event["version"]
    assert event.resource == event["resource"]
    assert event.path == event["path"]
    assert event.http_method == event["httpMethod"]
    assert event.headers == event["headers"]
    assert event.multi_value_headers == event["multiValueHeaders"]
    assert event.query_string_parameters == event["queryStringParameters"]
    assert event.multi_value_query_string_parameters == event["multiValueQueryStringParameters"]

    request_context = event.request_context
    assert request_context.account_id == event["requestContext"]["accountId"]
    assert request_context.api_id == event["requestContext"]["apiId"]

    authorizer = request_context.authorizer
    assert authorizer.claims is None
    assert authorizer.scopes is None

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

    assert event.path_parameters == event["pathParameters"]
    assert event.stage_variables == event["stageVariables"]
    assert event.body == event["body"]
    assert event.is_base64_encoded == event["isBase64Encoded"]

    assert request_context.connected_at is None
    assert request_context.connection_id is None
    assert request_context.event_type is None
    assert request_context.message_direction is None
    assert request_context.message_id is None
    assert request_context.route_key is None
    assert request_context.operation_name is None
    assert identity.api_key is None
    assert identity.api_key_id is None
    assert request_context.identity.client_cert.subject_dn == "www.example.com"


def test_api_gateway_proxy_event_with_principal_id():
    event = APIGatewayProxyEvent(load_event("apiGatewayProxyEventPrincipalId.json"))

    request_context = event.request_context
    authorizer = request_context.authorizer
    assert authorizer.claims is None
    assert authorizer.scopes is None
    assert authorizer["principalId"] == "fake"
    assert authorizer.get("principalId") == "fake"
    assert authorizer.principal_id == "fake"
    assert authorizer.integration_latency == 451
    assert authorizer.get("integrationStatus", "failed") == "failed"


def test_api_gateway_proxy_v2_event():
    event = APIGatewayProxyEventV2(load_event("apiGatewayProxyV2Event.json"))

    assert event.version == event["version"]
    assert event.route_key == event["routeKey"]
    assert event.raw_path == event["rawPath"]
    assert event.raw_query_string == event["rawQueryString"]
    assert event.cookies == event["cookies"]
    assert event.cookies[0] == "cookie1"
    assert event.headers == event["headers"]
    assert event.query_string_parameters == event["queryStringParameters"]
    assert event.query_string_parameters["parameter2"] == "value"

    request_context = event.request_context
    assert request_context.account_id == event["requestContext"]["accountId"]
    assert request_context.api_id == event["requestContext"]["apiId"]
    assert request_context.authorizer.jwt_claim == event["requestContext"]["authorizer"]["jwt"]["claims"]
    assert request_context.authorizer.jwt_scopes == event["requestContext"]["authorizer"]["jwt"]["scopes"]
    assert request_context.domain_name == event["requestContext"]["domainName"]
    assert request_context.domain_prefix == event["requestContext"]["domainPrefix"]

    http = request_context.http
    assert http.method == "POST"
    assert http.path == "/my/path"
    assert http.protocol == "HTTP/1.1"
    assert http.source_ip == "192.168.0.1/32"
    assert http.user_agent == "agent"

    assert request_context.request_id == event["requestContext"]["requestId"]
    assert request_context.route_key == event["requestContext"]["routeKey"]
    assert request_context.stage == event["requestContext"]["stage"]
    assert request_context.time == event["requestContext"]["time"]
    assert request_context.time_epoch == event["requestContext"]["timeEpoch"]
    assert request_context.authentication.subject_dn == "www.example.com"

    assert event.body == event["body"]
    assert event.path_parameters == event["pathParameters"]
    assert event.is_base64_encoded == event["isBase64Encoded"]
    assert event.stage_variables == event["stageVariables"]


def test_api_gateway_proxy_v2_lambda_authorizer_event():
    event = APIGatewayProxyEventV2(load_event("apiGatewayProxyV2LambdaAuthorizerEvent.json"))

    request_context = event.request_context
    assert request_context is not None
    lambda_props = request_context.authorizer.get_lambda
    assert lambda_props is not None
    assert lambda_props["key"] == "value"


def test_api_gateway_proxy_v2_iam_event():
    event = APIGatewayProxyEventV2(load_event("apiGatewayProxyV2IamEvent.json"))

    iam = event.request_context.authorizer.iam
    assert iam is not None
    assert iam.access_key == "ARIA2ZJZYVUEREEIHAKY"
    assert iam.account_id == "1234567890"
    assert iam.caller_id == "AROA7ZJZYVRE7C3DUXHH6:CognitoIdentityCredentials"
    assert iam.cognito_amr == ["foo"]
    assert iam.cognito_identity_id == "us-east-1:3f291106-8703-466b-8f2b-3ecee1ca56ce"
    assert iam.cognito_identity_pool_id == "us-east-1:4f291106-8703-466b-8f2b-3ecee1ca56ce"
    assert iam.principal_org_id == "AwsOrgId"
    assert iam.user_arn == "arn:aws:iam::1234567890:user/Admin"
    assert iam.user_id == "AROA2ZJZYVRE7Y3TUXHH6"
