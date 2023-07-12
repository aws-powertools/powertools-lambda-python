import pytest

from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    DENY_ALL_RESPONSE,
    APIGatewayAuthorizerResponse,
    APIGatewayAuthorizerTokenEvent,
    HttpVerb,
)


@pytest.fixture
def builder():
    return APIGatewayAuthorizerResponse("foo", "us-west-1", "123456789", "fantom", "dev")


def test_authorizer_response_no_statement(builder: APIGatewayAuthorizerResponse):
    # GIVEN a builder with no statements
    with pytest.raises(ValueError) as ex:
        # WHEN calling build
        builder.asdict()

    # THEN raise a name error for not statements
    assert str(ex.value) == "No statements defined for the policy"


def test_authorizer_response_invalid_verb(builder: APIGatewayAuthorizerResponse):
    with pytest.raises(ValueError, match="Invalid HTTP verb: 'INVALID'"):
        # GIVEN an invalid http_method
        # WHEN calling deny_method
        builder.deny_route(http_method="INVALID", resource="foo")


def test_authorizer_response_invalid_resource(builder: APIGatewayAuthorizerResponse):
    with pytest.raises(ValueError, match="Invalid resource path: \$."):  # noqa: W605
        # GIVEN an invalid resource path "$"
        # WHEN calling deny_method
        builder.deny_route(http_method=HttpVerb.GET.value, resource="$")


def test_authorizer_response_allow_all_routes_with_context():
    arn = "arn:aws:execute-api:us-west-1:123456789:fantom/dev/GET/foo"
    builder = APIGatewayAuthorizerResponse.from_route_arn(arn, principal_id="foo", context={"name": "Foo"})
    builder.allow_all_routes()
    assert builder.asdict() == {
        "principalId": "foo",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/*/*"],
                },
            ],
        },
        "context": {"name": "Foo"},
    }


def test_authorizer_response_allow_all_routes_with_usage_identifier_key():
    arn = "arn:aws:execute-api:us-east-1:1111111111:api/dev/ANY/y"
    builder = APIGatewayAuthorizerResponse.from_route_arn(arn, principal_id="cow", usage_identifier_key="key")
    builder.allow_all_routes()
    assert builder.asdict() == {
        "principalId": "cow",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": ["arn:aws:execute-api:us-east-1:1111111111:api/dev/*/*"],
                },
            ],
        },
        "usageIdentifierKey": "key",
    }


def test_authorizer_response_deny_all_routes(builder: APIGatewayAuthorizerResponse):
    builder.deny_all_routes()
    assert builder.asdict() == {
        "principalId": "foo",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/*/*"],
                },
            ],
        },
    }


def test_authorizer_response_allow_route(builder: APIGatewayAuthorizerResponse):
    builder.allow_route(http_method=HttpVerb.GET.value, resource="/foo")
    assert builder.asdict() == {
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/GET/foo"],
                },
            ],
        },
        "principalId": "foo",
    }


def test_authorizer_response_deny_route(builder: APIGatewayAuthorizerResponse):
    builder.deny_route(http_method=HttpVerb.PUT.value, resource="foo")
    assert builder.asdict() == {
        "principalId": "foo",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/PUT/foo"],
                },
            ],
        },
    }


def test_authorizer_response_allow_route_with_conditions(builder: APIGatewayAuthorizerResponse):
    condition = {"StringEquals": {"method.request.header.Content-Type": "text/html"}}
    builder.allow_route(
        http_method=HttpVerb.POST.value,
        resource="/foo",
        conditions=[condition],
    )
    assert builder.asdict() == {
        "principalId": "foo",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/POST/foo"],
                    "Condition": [{"StringEquals": {"method.request.header.Content-Type": "text/html"}}],
                },
            ],
        },
    }


def test_authorizer_response_deny_route_with_conditions(builder: APIGatewayAuthorizerResponse):
    condition = {"StringEquals": {"method.request.header.Content-Type": "application/json"}}
    builder.deny_route(http_method=HttpVerb.POST.value, resource="/foo", conditions=[condition])
    assert builder.asdict() == {
        "principalId": "foo",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/POST/foo"],
                    "Condition": [{"StringEquals": {"method.request.header.Content-Type": "application/json"}}],
                },
            ],
        },
    }


def test_deny_all():
    # CHECK we always explicitly deny all
    statements = DENY_ALL_RESPONSE["policyDocument"]["Statement"]
    assert len(statements) == 1
    assert statements[0] == {
        "Action": "execute-api:Invoke",
        "Effect": "Deny",
        "Resource": ["*"],
    }


def test_authorizer_response_allow_route_with_underscore(builder: APIGatewayAuthorizerResponse):
    builder.allow_route(http_method="GET", resource="/has_underscore")
    assert builder.asdict() == {
        "principalId": "foo",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/GET/has_underscore"],
                },
            ],
        },
    }


def test_parse_api_gateway_arn_with_resource():
    mock_event = {
        "type": "TOKEN",
        "methodArn": "arn:aws:execute-api:us-east-2:1234567890:abcd1234/latest/GET/path/part/part/1",
        "authorizationToken": "Bearer TOKEN",
    }
    event = APIGatewayAuthorizerTokenEvent(mock_event)
    event_arn = event.parsed_arn
    assert event_arn.resource == "path/part/part/1"

    authorizer_policy = APIGatewayAuthorizerResponse(
        principal_id="fooPrinciple",
        region=event_arn.region,
        aws_account_id=event_arn.aws_account_id,
        api_id=event_arn.api_id,
        stage=event_arn.stage,
    )
    authorizer_policy.allow_route(http_method=event_arn.http_method, resource=event_arn.resource)
    response = authorizer_policy.asdict()

    assert mock_event["methodArn"] == response["policyDocument"]["Statement"][0]["Resource"][0]
