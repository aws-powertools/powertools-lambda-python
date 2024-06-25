from aws_lambda_powertools.utilities.data_classes.s3_object_event import (
    S3ObjectLambdaEvent,
)
from tests.functional.utils import load_event


def test_s3_object_event_iam():
    raw_event = load_event("s3ObjectEventIAMUser.json")
    parsed_event = S3ObjectLambdaEvent(raw_event)

    assert parsed_event.request_id == "1a5ed718-5f53-471d-b6fe-5cf62d88d02a"
    assert parsed_event.object_context is not None
    object_context = parsed_event.object_context
    assert object_context.input_s3_url == raw_event["getObjectContext"]["inputS3Url"]
    assert object_context.output_route == raw_event["getObjectContext"]["outputRoute"]
    assert object_context.output_token == raw_event["getObjectContext"]["outputToken"]
    assert parsed_event.configuration is not None
    configuration = parsed_event.configuration
    assert configuration.access_point_arn == raw_event["configuration"]["accessPointArn"]
    assert configuration.supporting_access_point_arn == raw_event["configuration"]["supportingAccessPointArn"]
    assert configuration.payload == raw_event["configuration"]["payload"]
    assert parsed_event.user_request is not None
    user_request = parsed_event.user_request
    assert user_request.url == raw_event["userRequest"]["url"]
    assert user_request.headers == raw_event["userRequest"]["headers"]
    assert user_request.get_header_value("Accept-Encoding") == "identity"
    assert parsed_event.user_identity is not None
    user_identity = parsed_event.user_identity
    assert user_identity.get_type == raw_event["userIdentity"]["type"]
    assert user_identity.principal_id == raw_event["userIdentity"]["principalId"]
    assert user_identity.arn == raw_event["userIdentity"]["arn"]
    assert user_identity.account_id == raw_event["userIdentity"]["accountId"]
    assert user_identity.access_key_id == raw_event["userIdentity"]["accessKeyId"]
    assert user_identity.user_name == raw_event["userIdentity"]["userName"]
    assert user_identity.session_context is None
    assert parsed_event.protocol_version == raw_event["protocolVersion"]
    assert parsed_event.request_route == object_context.output_route
    assert parsed_event.request_token == object_context.output_token
    assert parsed_event.input_s3_url == object_context.input_s3_url


def test_s3_object_event_temp_credentials():
    raw_event = load_event("s3ObjectEventTempCredentials.json")
    parsed_event = S3ObjectLambdaEvent(raw_event)

    assert parsed_event.request_id == "requestId"
    session_context = parsed_event.user_identity.session_context
    assert session_context is not None
    session_issuer = session_context.session_issuer
    assert session_issuer is not None
    assert session_issuer.get_type == session_context["sessionIssuer"]["type"]
    assert session_issuer.user_name == session_context["sessionIssuer"]["userName"]
    assert session_issuer.principal_id == session_context["sessionIssuer"]["principalId"]
    assert session_issuer.arn == session_context["sessionIssuer"]["arn"]
    assert session_issuer.account_id == session_context["sessionIssuer"]["accountId"]
    session_attributes = session_context.attributes
    assert session_attributes is not None
    assert session_attributes.mfa_authenticated == session_context["attributes"]["mfaAuthenticated"]
    assert session_attributes.creation_date == session_context["attributes"]["creationDate"]
