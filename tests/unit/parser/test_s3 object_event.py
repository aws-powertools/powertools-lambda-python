from aws_lambda_powertools.utilities.parser.models import S3ObjectLambdaEvent
from tests.functional.utils import load_event


def test_s3_object_event():
    event = load_event("s3ObjectEventIAMUser.json")
    parsed_event: S3ObjectLambdaEvent = S3ObjectLambdaEvent(**event)
    assert parsed_event.xAmzRequestId == event["xAmzRequestId"]
    assert parsed_event.getObjectContext is not None
    object_context = parsed_event.getObjectContext
    assert str(object_context.inputS3Url) == event["getObjectContext"]["inputS3Url"]
    assert object_context.outputRoute == event["getObjectContext"]["outputRoute"]
    assert object_context.outputToken == event["getObjectContext"]["outputToken"]
    assert parsed_event.configuration is not None
    configuration = parsed_event.configuration
    assert configuration.accessPointArn == event["configuration"]["accessPointArn"]
    assert configuration.supportingAccessPointArn == event["configuration"]["supportingAccessPointArn"]
    assert configuration.payload == event["configuration"]["payload"]
    assert parsed_event.userRequest is not None
    user_request = parsed_event.userRequest
    assert user_request.url == event["userRequest"]["url"]
    assert user_request.headers == event["userRequest"]["headers"]
    assert user_request.headers["Accept-Encoding"] == "identity"
    assert parsed_event.userIdentity is not None
    user_identity = parsed_event.userIdentity
    assert user_identity.type == event["userIdentity"]["type"]
    assert user_identity.principalId == event["userIdentity"]["principalId"]
    assert user_identity.arn == event["userIdentity"]["arn"]
    assert user_identity.accountId == event["userIdentity"]["accountId"]
    assert user_identity.accessKeyId == event["userIdentity"]["accessKeyId"]
    assert user_identity.userName == event["userIdentity"]["userName"]
    assert user_identity.sessionContext is None
    assert parsed_event.protocolVersion == event["protocolVersion"]


def test_s3_object_event_temp_credentials():
    event = load_event("s3ObjectEventTempCredentials.json")
    parsed_event: S3ObjectLambdaEvent = S3ObjectLambdaEvent(**event)
    assert parsed_event.xAmzRequestId == event["xAmzRequestId"]
    session_context = parsed_event.userIdentity.sessionContext
    assert session_context is not None
    session_issuer = session_context.sessionIssuer
    session_issuer_raw = event["userIdentity"]["sessionContext"]["sessionIssuer"]
    assert session_issuer is not None
    assert session_issuer.type == session_issuer_raw["type"]
    assert session_issuer.userName == session_issuer_raw["userName"]
    assert session_issuer.principalId == session_issuer_raw["principalId"]
    assert session_issuer.arn == session_issuer_raw["arn"]
    assert session_issuer.accountId == session_issuer_raw["accountId"]
    session_attributes = session_context.attributes
    session_attributes_raw = event["userIdentity"]["sessionContext"]["attributes"]
    assert session_attributes is not None
    assert str(session_attributes.mfaAuthenticated).lower() == session_attributes_raw["mfaAuthenticated"]
    assert session_attributes.creationDate == session_attributes_raw["creationDate"]
