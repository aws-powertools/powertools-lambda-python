from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.data_classes.appsync_resolver_event import (
    AppSyncIdentityCognito,
    AppSyncIdentityIAM,
    AppSyncResolverEventInfo,
    get_identity_object,
)
from tests.functional.utils import load_event


def test_appsync_resolver_event():
    raw_event = load_event("appSyncResolverEvent.json")
    parsed_event = AppSyncResolverEvent(raw_event)

    assert parsed_event.type_name == raw_event["typeName"]
    assert parsed_event.field_name == raw_event["fieldName"]
    assert parsed_event.arguments.get("name") == raw_event["arguments"]["name"]
    assert parsed_event.identity.claims.get("token_use") == raw_event["identity"]["claims"]["token_use"]
    assert parsed_event.source.get("name") == raw_event["source"]["name"]
    assert parsed_event.get_header_value("X-amzn-trace-id") == "Root=1-60488877-0b0c4e6727ab2a1c545babd0"
    assert parsed_event.get_header_value("X-amzn-trace-id", case_sensitive=True) is None
    assert parsed_event.get_header_value("missing", default_value="Foo") == "Foo"
    assert parsed_event.prev_result == {}
    assert parsed_event.stash is None

    info = parsed_event.info
    assert info is not None
    assert isinstance(info, AppSyncResolverEventInfo)
    assert info.field_name == raw_event["fieldName"]
    assert info.parent_type_name == raw_event["typeName"]
    assert info.variables is None
    assert info.selection_set_list is None
    assert info.selection_set_graphql is None

    assert isinstance(parsed_event.identity, AppSyncIdentityCognito)
    identity: AppSyncIdentityCognito = parsed_event.identity
    raw_identity = raw_event["identity"]
    assert identity.claims is not None
    assert identity.sub == raw_identity["claims"]["sub"]
    assert len(identity.source_ip) == 1
    assert identity.username == raw_identity["username"]
    assert identity.default_auth_strategy == raw_identity["defaultAuthStrategy"]
    assert identity.groups is None
    assert identity.issuer == raw_identity["issuer"]


def test_get_identity_object_is_none():
    assert get_identity_object(None) is None

    event = AppSyncResolverEvent({})
    assert event.identity is None


def test_get_identity_object_iam():
    identity = {
        "accountId": "string",
        "cognitoIdentityPoolId": "string",
        "cognitoIdentityId": "string",
        "sourceIp": ["string"],
        "username": "string",
        "userArn": "string",
        "cognitoIdentityAuthType": "string",
        "cognitoIdentityAuthProvider": "string",
    }

    identity_object = get_identity_object(identity)

    assert isinstance(identity_object, AppSyncIdentityIAM)
    assert identity_object.account_id == identity["accountId"]
    assert identity_object.cognito_identity_pool_id == identity["cognitoIdentityPoolId"]
    assert identity_object.cognito_identity_id == identity["cognitoIdentityId"]
    assert identity_object.source_ip == identity["sourceIp"]
    assert identity_object.username == identity["username"]
    assert identity_object.user_arn == identity["userArn"]
    assert identity_object.cognito_identity_auth_type == identity["cognitoIdentityAuthType"]
    assert identity_object.cognito_identity_auth_provider == identity["cognitoIdentityAuthProvider"]


def test_appsync_resolver_direct():
    raw_event = load_event("appSyncDirectResolver.json")
    parsed_event = AppSyncResolverEvent(raw_event)

    assert parsed_event.source is None
    assert parsed_event.arguments.get("id") == raw_event["arguments"]["id"]
    assert parsed_event.stash == {}
    assert parsed_event.prev_result is None
    assert isinstance(parsed_event.identity, AppSyncIdentityCognito)

    info = parsed_event.info
    info_raw = raw_event["info"]
    assert info is not None
    assert isinstance(info, AppSyncResolverEventInfo)
    assert info.selection_set_list is not None
    assert info.selection_set_list == info["selectionSetList"]
    assert info.selection_set_graphql == info_raw["selectionSetGraphQL"]
    assert info.parent_type_name == info_raw["parentTypeName"]
    assert info.field_name == info_raw["fieldName"]

    assert parsed_event.type_name == info.parent_type_name
    assert parsed_event.field_name == info.field_name


def test_appsync_resolver_event_info():
    info_dict = {
        "fieldName": "getPost",
        "parentTypeName": "Query",
        "variables": {"postId": "123", "authorId": "456"},
        "selectionSetList": ["postId", "title"],
        "selectionSetGraphQL": "{\n  getPost(id: $postId) {\n    postId\n  etc..",
    }
    event = {"info": info_dict}

    event = AppSyncResolverEvent(event)

    assert event.source is None
    assert event.identity is None
    assert event.info is not None
    assert isinstance(event.info, AppSyncResolverEventInfo)
    info: AppSyncResolverEventInfo = event.info
    assert info.field_name == info_dict["fieldName"]
    assert event.field_name == info.field_name
    assert info.parent_type_name == info_dict["parentTypeName"]
    assert event.type_name == info.parent_type_name
    assert info.variables == info_dict["variables"]
    assert info.variables["postId"] == "123"
    assert info.selection_set_list == info_dict["selectionSetList"]
    assert info.selection_set_graphql == info_dict["selectionSetGraphQL"]


def test_appsync_resolver_event_empty():
    event = AppSyncResolverEvent({})

    assert event.info.field_name is None
    assert event.info.parent_type_name is None
