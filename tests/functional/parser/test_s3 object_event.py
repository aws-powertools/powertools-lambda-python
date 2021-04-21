from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.parser.models import S3ObjectLambdaEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.utils import load_event


@event_parser(model=S3ObjectLambdaEvent)
def handle_s3_object_event_iam(event: S3ObjectLambdaEvent, _: LambdaContext):
    return event


def test_s3_object_event():
    event = load_event("s3ObjectEventIAMUser.json")
    parsed_event: S3ObjectLambdaEvent = handle_s3_object_event_iam(event, LambdaContext())
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


@event_parser(model=S3ObjectLambdaEvent)
def handle_s3_object_event_temp_creds(event: S3ObjectLambdaEvent, _: LambdaContext):
    return event


def test_s3_object_event_temp_credentials():
    event = load_event("s3ObjectEventTempCredentials.json")
    parsed_event: S3ObjectLambdaEvent = handle_s3_object_event_temp_creds(event, LambdaContext())
    assert parsed_event.xAmzRequestId == event["xAmzRequestId"]
    session_context = parsed_event.userIdentity.sessionContext
    assert session_context is not None
    session_issuer = session_context.sessionIssuer
    assert session_issuer is not None
    assert session_issuer.type == event["userIdentity"]["sessionContext"]["sessionIssuer"]["type"]
    assert session_issuer.userName == event["userIdentity"]["sessionContext"]["sessionIssuer"]["userName"]
    assert session_issuer.principalId == event["userIdentity"]["sessionContext"]["sessionIssuer"]["principalId"]
    assert session_issuer.arn == event["userIdentity"]["sessionContext"]["sessionIssuer"]["arn"]
    assert session_issuer.accountId == event["userIdentity"]["sessionContext"]["sessionIssuer"]["accountId"]
    session_attributes = session_context.attributes
    assert session_attributes is not None
    assert (
        str(session_attributes.mfaAuthenticated).lower()
        == event["userIdentity"]["sessionContext"]["attributes"]["mfaAuthenticated"]
    )
    assert session_attributes.creationDate == event["userIdentity"]["sessionContext"]["attributes"]["creationDate"]
