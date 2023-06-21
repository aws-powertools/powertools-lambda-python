from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
    APIGatewayProxyEventV2,
)
from tests.functional.utils import load_event


def test_default_api_gateway_proxy_event():
    raw_event = load_event("apiGatewayProxyEvent_noVersionAuth.json")
    parsed_event = APIGatewayProxyEvent(raw_event)

    assert raw_event.get("version") is None
    assert parsed_event.resource == raw_event["resource"]
    assert parsed_event.path == raw_event["path"]
    assert parsed_event.http_method == raw_event["httpMethod"]
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.multi_value_headers == raw_event["multiValueHeaders"]
    assert parsed_event.query_string_parameters == raw_event["queryStringParameters"]
    assert parsed_event.multi_value_query_string_parameters == raw_event["multiValueQueryStringParameters"]

    request_context = parsed_event.request_context
    request_context_raw = raw_event["requestContext"]
    assert request_context.account_id == request_context_raw["accountId"]
    assert request_context.api_id == request_context_raw["apiId"]

    assert request_context.get("authorizer") is None

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

    assert parsed_event.path_parameters == raw_event["pathParameters"]
    assert parsed_event.stage_variables == raw_event["stageVariables"]
    assert parsed_event.body == raw_event["body"]
    assert parsed_event.is_base64_encoded == raw_event["isBase64Encoded"]

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
    raw_event = load_event("apiGatewayProxyEvent.json")
    parsed_event = APIGatewayProxyEvent(raw_event)

    assert parsed_event.version == raw_event["version"]
    assert parsed_event.resource == raw_event["resource"]
    assert parsed_event.path == raw_event["path"]
    assert parsed_event.http_method == raw_event["httpMethod"]
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.multi_value_headers == raw_event["multiValueHeaders"]
    assert parsed_event.query_string_parameters == raw_event["queryStringParameters"]
    assert parsed_event.multi_value_query_string_parameters == raw_event["multiValueQueryStringParameters"]

    request_context = parsed_event.request_context
    request_context_raw = raw_event["requestContext"]
    assert request_context.account_id == request_context_raw["accountId"]
    assert request_context.api_id == request_context_raw["apiId"]

    authorizer = request_context.authorizer
    assert authorizer.claims is None
    assert authorizer.scopes is None

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

    assert parsed_event.path_parameters == raw_event["pathParameters"]
    assert parsed_event.stage_variables == raw_event["stageVariables"]
    assert parsed_event.body == raw_event["body"]
    assert parsed_event.is_base64_encoded == raw_event["isBase64Encoded"]

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
    raw_event = load_event("apiGatewayProxyEventPrincipalId.json")
    parsed_event = APIGatewayProxyEvent(raw_event)

    request_context = parsed_event.request_context
    authorizer = request_context.authorizer
    assert authorizer.claims is None
    assert authorizer.scopes is None
    assert authorizer.principal_id == raw_event["requestContext"]["authorizer"]["principalId"]
    assert authorizer.integration_latency == raw_event["requestContext"]["authorizer"]["integrationLatency"]
    assert authorizer.get("integrationStatus", "failed") == "failed"


def test_api_gateway_proxy_v2_event():
    raw_event = load_event("apiGatewayProxyV2Event.json")
    parsed_event = APIGatewayProxyEventV2(raw_event)

    assert parsed_event.version == raw_event["version"]
    assert parsed_event.route_key == raw_event["routeKey"]
    assert parsed_event.raw_path == raw_event["rawPath"]
    assert parsed_event.raw_query_string == raw_event["rawQueryString"]
    assert parsed_event.cookies == raw_event["cookies"]
    assert parsed_event.cookies[0] == "cookie1"
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.query_string_parameters == raw_event["queryStringParameters"]
    assert parsed_event.query_string_parameters["parameter2"] == "value"

    request_context = parsed_event.request_context
    request_context_raw = raw_event["requestContext"]
    assert request_context.account_id == request_context_raw["accountId"]
    assert request_context.api_id == request_context_raw["apiId"]
    assert request_context.authorizer.jwt_claim == request_context_raw["authorizer"]["jwt"]["claims"]
    assert request_context.authorizer.jwt_scopes == request_context_raw["authorizer"]["jwt"]["scopes"]
    assert request_context.domain_name == request_context_raw["domainName"]
    assert request_context.domain_prefix == request_context_raw["domainPrefix"]
    assert request_context.request_id == request_context_raw["requestId"]
    assert request_context.route_key == request_context_raw["routeKey"]
    assert request_context.stage == request_context_raw["stage"]
    assert request_context.time == request_context_raw["time"]
    assert request_context.time_epoch == request_context_raw["timeEpoch"]
    assert request_context.authentication.subject_dn == "www.example.com"

    http = request_context.http
    http_raw = raw_event["requestContext"]["http"]
    assert http.method == http_raw["method"]
    assert http.path == http_raw["path"]
    assert http.protocol == http_raw["protocol"]
    assert http.source_ip == http_raw["sourceIp"]
    assert http.user_agent == http_raw["userAgent"]

    assert parsed_event.body == raw_event["body"]
    assert parsed_event.path_parameters == raw_event["pathParameters"]
    assert parsed_event.is_base64_encoded == raw_event["isBase64Encoded"]
    assert parsed_event.stage_variables == raw_event["stageVariables"]


def test_api_gateway_proxy_v2_lambda_authorizer_event():
    raw_event = load_event("apiGatewayProxyV2LambdaAuthorizerEvent.json")
    parsed_event = APIGatewayProxyEventV2(raw_event)

    request_context = parsed_event.request_context
    assert request_context is not None
    lambda_props = request_context.authorizer.get_lambda
    assert lambda_props is not None
    assert lambda_props.get("key") == "value"


def test_api_gateway_proxy_v2_iam_event():
    raw_event = load_event("apiGatewayProxyV2IamEvent.json")
    parsed_event = APIGatewayProxyEventV2(raw_event)

    iam = parsed_event.request_context.authorizer.iam
    iam_raw = raw_event["requestContext"]["authorizer"]["iam"]
    assert iam is not None
    assert iam.access_key == iam_raw["accessKey"]
    assert iam.account_id == iam_raw["accountId"]
    assert iam.caller_id == iam_raw["callerId"]
    assert iam.cognito_amr == ["foo"]
    assert iam.cognito_identity_id == iam_raw["cognitoIdentity"]["identityId"]
    assert iam.cognito_identity_pool_id == iam_raw["cognitoIdentity"]["identityPoolId"]
    assert iam.principal_org_id == iam_raw["principalOrgId"]
    assert iam.user_arn == iam_raw["userArn"]
    assert iam.user_id == iam_raw["userId"]
