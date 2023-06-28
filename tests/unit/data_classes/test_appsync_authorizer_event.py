from aws_lambda_powertools.utilities.data_classes.appsync_authorizer_event import (
    AppSyncAuthorizerEvent,
    AppSyncAuthorizerResponse,
)
from tests.functional.utils import load_event


def test_appsync_authorizer_event():
    raw_event = load_event("appSyncAuthorizerEvent.json")
    parsed_event = AppSyncAuthorizerEvent(raw_event)

    assert parsed_event.authorization_token == raw_event["authorizationToken"]
    assert parsed_event.request_context.api_id == raw_event["requestContext"]["apiId"]
    assert parsed_event.request_context.account_id == raw_event["requestContext"]["accountId"]
    assert parsed_event.request_context.request_id == raw_event["requestContext"]["requestId"]
    assert parsed_event.request_context.query_string == raw_event["requestContext"]["queryString"]
    assert parsed_event.request_context.operation_name == raw_event["requestContext"]["operationName"]
    assert parsed_event.request_context.variables == raw_event["requestContext"]["variables"]


def test_appsync_authorizer_response():
    """Check various helper functions for AppSync authorizer response"""
    expected = load_event("appSyncAuthorizerResponse.json")
    response = AppSyncAuthorizerResponse(
        authorize=True,
        max_age=15,
        resolver_context={"balance": 100, "name": "Foo Man"},
        deny_fields=["Mutation.createEvent"],
    )
    assert expected == response.asdict()

    assert {"isAuthorized": False} == AppSyncAuthorizerResponse().asdict()
    assert {"isAuthorized": False} == AppSyncAuthorizerResponse(deny_fields=[]).asdict()
    assert {"isAuthorized": False} == AppSyncAuthorizerResponse(resolver_context={}).asdict()
    assert {"isAuthorized": True} == AppSyncAuthorizerResponse(authorize=True).asdict()
    assert {"isAuthorized": False, "ttlOverride": 0} == AppSyncAuthorizerResponse(max_age=0).asdict()
