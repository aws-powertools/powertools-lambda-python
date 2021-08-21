import pytest

from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    APIGatewayAuthorizerResponse,
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
    with pytest.raises(ValueError) as ex:
        # GIVEN a invalid http_method
        # WHEN calling deny_method
        builder.deny_route("INVALID", "foo")

    # THEN raise a name error for invalid http verb
    assert str(ex.value) == "Invalid HTTP verb INVALID. Allowed verbs in HttpVerb class"


def test_authorizer_response_invalid_resource(builder: APIGatewayAuthorizerResponse):
    with pytest.raises(ValueError) as ex:
        # GIVEN a invalid resource path "$"
        # WHEN calling deny_method
        builder.deny_route(HttpVerb.GET, "$")

    # THEN raise a name error for invalid resource
    assert "Invalid resource path: $" in str(ex.value)


def test_authorizer_response_allow_all_routes_with_context():
    builder = APIGatewayAuthorizerResponse("foo", "us-west-1", "123456789", "fantom", "dev", {"name": "Foo"})
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
                }
            ],
        },
        "context": {"name": "Foo"},
    }


def test_authorizer_response_deny_all_routes(builder: APIGatewayAuthorizerResponse):
    builder.deny_all_route()
    assert builder.asdict() == {
        "principalId": "foo",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/*/*"],
                }
            ],
        },
    }


def test_authorizer_response_allow_route(builder: APIGatewayAuthorizerResponse):
    builder.allow_route(HttpVerb.GET, "/foo")
    assert builder.asdict() == {
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/GET/foo"],
                }
            ],
        },
        "principalId": "foo",
    }


def test_authorizer_response_deny_route(builder: APIGatewayAuthorizerResponse):
    builder.deny_route(HttpVerb.PUT, "foo")
    assert builder.asdict() == {
        "principalId": "foo",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": ["arn:aws:execute-api:us-west-1:123456789:fantom/dev/PUT/foo"],
                }
            ],
        },
    }


def test_authorizer_response_allow_route_with_conditions(builder: APIGatewayAuthorizerResponse):
    builder.allow_route(
        HttpVerb.POST,
        "/foo",
        [
            {"StringEquals": {"method.request.header.Content-Type": "text/html"}},
        ],
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
                }
            ],
        },
    }


def test_authorizer_response_deny_route_with_conditions(builder: APIGatewayAuthorizerResponse):
    builder.deny_route(
        HttpVerb.POST,
        "/foo",
        [
            {"StringEquals": {"method.request.header.Content-Type": "application/json"}},
        ],
    )
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
                }
            ],
        },
    }
