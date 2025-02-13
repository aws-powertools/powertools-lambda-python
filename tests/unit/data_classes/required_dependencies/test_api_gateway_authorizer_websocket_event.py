import pytest

from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    DENY_ALL_RESPONSE,
    APIGatewayAuthorizerResponseWebSocket,
)


@pytest.fixture
def builder():
    return APIGatewayAuthorizerResponseWebSocket("foo", "us-west-1", "123456789", "fantom", "dev")


def test_authorizer_response_no_statement(builder: APIGatewayAuthorizerResponseWebSocket):
    # GIVEN a builder with no statements
    with pytest.raises(ValueError) as ex:
        # WHEN calling build
        builder.asdict()

    # THEN raise a name error for not statements
    assert str(ex.value) == "No statements defined for the policy"


def test_authorizer_response_allow_all_routes_with_context():
    arn = "arn:aws:execute-api:us-west-1:123456789:fantom/dev/$connect"
    builder = APIGatewayAuthorizerResponseWebSocket.from_route_arn(arn, principal_id="foo", context={"name": "Foo"})
    builder.allow_all_routes()
    assert builder.asdict() == {
        "principalId": "foo",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/*"],
                },
            ],
        },
        "context": {"name": "Foo"},
    }


def test_authorizer_response_allow_all_routes_with_usage_identifier_key():
    arn = "arn:aws:execute-api:us-east-1:1111111111:api/dev/y"
    builder = APIGatewayAuthorizerResponseWebSocket.from_route_arn(arn, principal_id="cow", usage_identifier_key="key")
    builder.allow_all_routes()
    assert builder.asdict() == {
        "principalId": "cow",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": ["arn:aws:execute-api:us-east-1:1111111111:api/dev/*"],
                },
            ],
        },
        "usageIdentifierKey": "key",
    }


def test_authorizer_response_deny_all_routes(builder: APIGatewayAuthorizerResponseWebSocket):
    builder.deny_all_routes()
    assert builder.asdict() == {
        "principalId": "foo",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/*"],
                },
            ],
        },
    }


def test_authorizer_response_allow_route(builder: APIGatewayAuthorizerResponseWebSocket):
    builder.allow_route(resource="/foo")
    assert builder.asdict() == {
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/foo"],
                },
            ],
        },
        "principalId": "foo",
    }


def test_authorizer_response_deny_route(builder: APIGatewayAuthorizerResponseWebSocket):
    builder.deny_route(resource="foo")
    assert builder.asdict() == {
        "principalId": "foo",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/foo"],
                },
            ],
        },
    }


def test_authorizer_response_allow_route_with_conditions(builder: APIGatewayAuthorizerResponseWebSocket):
    condition = {"StringEquals": {"method.request.header.Content-Type": "text/html"}}
    builder.allow_route(
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
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/foo"],
                    "Condition": [{"StringEquals": {"method.request.header.Content-Type": "text/html"}}],
                },
            ],
        },
    }


def test_authorizer_response_deny_route_with_conditions(builder: APIGatewayAuthorizerResponseWebSocket):
    condition = {"StringEquals": {"method.request.header.Content-Type": "application/json"}}
    builder.deny_route(resource="/foo", conditions=[condition])
    assert builder.asdict() == {
        "principalId": "foo",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/foo"],
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


def test_authorizer_response_allow_route_with_underscore(builder: APIGatewayAuthorizerResponseWebSocket):
    builder.allow_route(resource="/has_underscore")
    assert builder.asdict() == {
        "principalId": "foo",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/has_underscore"],
                },
            ],
        },
    }
