from aws_lambda_powertools.utilities.data_classes.appsync_authorizer_event import (
    AppSyncAuthorizerEvent,
    AppSyncAuthorizerResponse,
)
from tests.functional.utils import load_event


def test_appsync_authorizer_event():
    event = AppSyncAuthorizerEvent(load_event("appSyncAuthorizerEvent.json"))

    assert event.authorization_token == "BE9DC5E3-D410-4733-AF76-70178092E681"
    assert event.authorization_token == event["authorizationToken"]
    assert event.request_context.api_id == event["requestContext"]["apiId"]
    assert event.request_context.account_id == event["requestContext"]["accountId"]
    assert event.request_context.request_id == event["requestContext"]["requestId"]
    assert event.request_context.query_string == event["requestContext"]["queryString"]
    assert event.request_context.operation_name == event["requestContext"]["operationName"]
    assert event.request_context.variables == event["requestContext"]["variables"]


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
