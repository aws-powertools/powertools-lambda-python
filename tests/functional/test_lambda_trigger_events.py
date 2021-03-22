import base64
import json
import os
from secrets import compare_digest
from urllib.parse import quote_plus

from aws_lambda_powertools.utilities.data_classes import (
    ALBEvent,
    APIGatewayProxyEvent,
    APIGatewayProxyEventV2,
    AppSyncResolverEvent,
    CloudWatchLogsEvent,
    EventBridgeEvent,
    KinesisStreamEvent,
    S3Event,
    SESEvent,
    SNSEvent,
    SQSEvent,
)
from aws_lambda_powertools.utilities.data_classes.appsync_resolver_event import (
    AppSyncIdentityCognito,
    AppSyncIdentityIAM,
    AppSyncResolverEventInfo,
    get_identity_object,
)
from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import (
    CreateAuthChallengeTriggerEvent,
    CustomMessageTriggerEvent,
    DefineAuthChallengeTriggerEvent,
    PostAuthenticationTriggerEvent,
    PostConfirmationTriggerEvent,
    PreAuthenticationTriggerEvent,
    PreSignUpTriggerEvent,
    PreTokenGenerationTriggerEvent,
    UserMigrationTriggerEvent,
    VerifyAuthChallengeResponseTriggerEvent,
)
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent, DictWrapper
from aws_lambda_powertools.utilities.data_classes.connect_contact_flow_event import (
    ConnectContactFlowChannel,
    ConnectContactFlowEndpointType,
    ConnectContactFlowEvent,
    ConnectContactFlowInitiationMethod,
)
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    AttributeValue,
    DynamoDBRecordEventName,
    DynamoDBStreamEvent,
    StreamViewType,
)
from aws_lambda_powertools.utilities.data_classes.s3_object_event import S3ObjectLambdaEvent


def load_event(file_name: str) -> dict:
    full_file_name = os.path.dirname(os.path.realpath(__file__)) + "/../events/" + file_name
    with open(full_file_name) as fp:
        return json.load(fp)


def test_dict_wrapper_equals():
    class DataClassSample(DictWrapper):
        @property
        def message(self) -> str:
            return self.get("message")

    data1 = {"message": "foo1"}
    data2 = {"message": "foo2"}

    assert DataClassSample(data1) == DataClassSample(data1)
    assert DataClassSample(data1) != DataClassSample(data2)
    # Comparing against a dict should not be equals
    assert DataClassSample(data1) != data1
    assert data1 != DataClassSample(data1)
    assert DataClassSample(data1) is not data1
    assert data1 is not DataClassSample(data1)

    assert DataClassSample(data1).raw_event is data1


def test_cloud_watch_trigger_event():
    event = CloudWatchLogsEvent(load_event("cloudWatchLogEvent.json"))

    decompressed_logs_data = event.decompress_logs_data
    assert event.decompress_logs_data == decompressed_logs_data

    json_logs_data = event.parse_logs_data()
    assert event.parse_logs_data().raw_event == json_logs_data.raw_event
    log_events = json_logs_data.log_events
    log_event = log_events[0]

    assert json_logs_data.owner == "123456789123"
    assert json_logs_data.log_group == "testLogGroup"
    assert json_logs_data.log_stream == "testLogStream"
    assert json_logs_data.subscription_filters == ["testFilter"]
    assert json_logs_data.message_type == "DATA_MESSAGE"

    assert log_event.get_id == "eventId1"
    assert log_event.timestamp == 1440442987000
    assert log_event.message == "[ERROR] First test message"
    assert log_event.extracted_fields is None

    event2 = CloudWatchLogsEvent(load_event("cloudWatchLogEvent.json"))
    assert event.raw_event == event2.raw_event


def test_cognito_pre_signup_trigger_event():
    event = PreSignUpTriggerEvent(load_event("cognitoPreSignUpEvent.json"))

    # Verify BaseTriggerEvent properties
    assert event.version == "string"
    assert event.trigger_source == "PreSignUp_SignUp"
    assert event.region == "us-east-1"
    assert event.user_pool_id == "string"
    assert event.user_name == "userName"
    caller_context = event.caller_context
    assert caller_context.aws_sdk_version == "awsSdkVersion"
    assert caller_context.client_id == "clientId"

    # Verify properties
    user_attributes = event.request.user_attributes
    assert user_attributes["email"] == "user@example.com"
    assert event.request.validation_data is None
    assert event.request.client_metadata is None

    # Verify setters
    event.response.auto_confirm_user = True
    assert event.response.auto_confirm_user is True
    event.response.auto_verify_phone = True
    assert event.response.auto_verify_phone is True
    event.response.auto_verify_email = True
    assert event.response.auto_verify_email is True
    assert event["response"]["autoVerifyEmail"] is True


def test_cognito_post_confirmation_trigger_event():
    event = PostConfirmationTriggerEvent(load_event("cognitoPostConfirmationEvent.json"))

    assert event.trigger_source == "PostConfirmation_ConfirmSignUp"

    user_attributes = event.request.user_attributes
    assert user_attributes["email"] == "user@example.com"
    assert event.request.client_metadata is None


def test_cognito_user_migration_trigger_event():
    event = UserMigrationTriggerEvent(load_event("cognitoUserMigrationEvent.json"))

    assert event.trigger_source == "UserMigration_Authentication"

    assert compare_digest(event.request.password, event["request"]["password"])
    assert event.request.validation_data is None
    assert event.request.client_metadata is None

    event.response.user_attributes = {"username": "username"}
    assert event.response.user_attributes == event["response"]["userAttributes"]
    assert event.response.user_attributes == {"username": "username"}
    assert event.response.final_user_status is None
    assert event.response.message_action is None
    assert event.response.force_alias_creation is None
    assert event.response.desired_delivery_mediums is None

    event.response.final_user_status = "CONFIRMED"
    assert event.response.final_user_status == "CONFIRMED"
    event.response.message_action = "SUPPRESS"
    assert event.response.message_action == "SUPPRESS"
    event.response.force_alias_creation = True
    assert event.response.force_alias_creation is True
    event.response.desired_delivery_mediums = ["EMAIL"]
    assert event.response.desired_delivery_mediums == ["EMAIL"]


def test_cognito_custom_message_trigger_event():
    event = CustomMessageTriggerEvent(load_event("cognitoCustomMessageEvent.json"))

    assert event.trigger_source == "CustomMessage_AdminCreateUser"

    assert event.request.code_parameter == "####"
    assert event.request.username_parameter == "username"
    assert event.request.user_attributes["phone_number_verified"] is False
    assert event.request.client_metadata is None

    event.response.sms_message = "sms"
    assert event.response.sms_message == event["response"]["smsMessage"]
    event.response.email_message = "email"
    assert event.response.email_message == event["response"]["emailMessage"]
    event.response.email_subject = "subject"
    assert event.response.email_subject == event["response"]["emailSubject"]


def test_cognito_pre_authentication_trigger_event():
    event = PreAuthenticationTriggerEvent(load_event("cognitoPreAuthenticationEvent.json"))

    assert event.trigger_source == "PreAuthentication_Authentication"

    assert event.request.user_not_found is None
    event["request"]["userNotFound"] = True
    assert event.request.user_not_found is True
    assert event.request.user_attributes["email"] == "pre-auth@mail.com"
    assert event.request.validation_data is None


def test_cognito_post_authentication_trigger_event():
    event = PostAuthenticationTriggerEvent(load_event("cognitoPostAuthenticationEvent.json"))

    assert event.trigger_source == "PostAuthentication_Authentication"

    assert event.request.new_device_used is True
    assert event.request.user_attributes["email"] == "post-auth@mail.com"
    assert event.request.client_metadata is None


def test_cognito_pre_token_generation_trigger_event():
    event = PreTokenGenerationTriggerEvent(load_event("cognitoPreTokenGenerationEvent.json"))

    assert event.trigger_source == "TokenGeneration_Authentication"

    group_configuration = event.request.group_configuration
    assert group_configuration.groups_to_override == []
    assert group_configuration.iam_roles_to_override == []
    assert group_configuration.preferred_role is None
    assert event.request.user_attributes["email"] == "test@mail.com"
    assert event.request.client_metadata is None

    event["request"]["groupConfiguration"]["preferredRole"] = "temp"
    group_configuration = event.request.group_configuration
    assert group_configuration.preferred_role == "temp"

    assert event["response"].get("claimsOverrideDetails") is None
    claims_override_details = event.response.claims_override_details
    assert event["response"]["claimsOverrideDetails"] == {}

    assert claims_override_details.claims_to_add_or_override is None
    assert claims_override_details.claims_to_suppress is None
    assert claims_override_details.group_configuration is None

    claims_override_details.group_configuration = {}
    assert claims_override_details.group_configuration._data == {}
    assert event["response"]["claimsOverrideDetails"]["groupOverrideDetails"] == {}

    expected_claims = {"test": "value"}
    claims_override_details.claims_to_add_or_override = expected_claims
    assert claims_override_details.claims_to_add_or_override["test"] == "value"
    assert event["response"]["claimsOverrideDetails"]["claimsToAddOrOverride"] == expected_claims

    claims_override_details.claims_to_suppress = ["email"]
    assert claims_override_details.claims_to_suppress[0] == "email"
    assert event["response"]["claimsOverrideDetails"]["claimsToSuppress"] == ["email"]

    expected_groups = ["group-A", "group-B"]
    claims_override_details.set_group_configuration_groups_to_override(expected_groups)
    assert claims_override_details.group_configuration.groups_to_override == expected_groups
    assert event["response"]["claimsOverrideDetails"]["groupOverrideDetails"]["groupsToOverride"] == expected_groups

    claims_override_details.set_group_configuration_iam_roles_to_override(["role"])
    assert claims_override_details.group_configuration.iam_roles_to_override == ["role"]
    assert event["response"]["claimsOverrideDetails"]["groupOverrideDetails"]["iamRolesToOverride"] == ["role"]

    claims_override_details.set_group_configuration_preferred_role("role_name")
    assert claims_override_details.group_configuration.preferred_role == "role_name"
    assert event["response"]["claimsOverrideDetails"]["groupOverrideDetails"]["preferredRole"] == "role_name"


def test_cognito_define_auth_challenge_trigger_event():
    event = DefineAuthChallengeTriggerEvent(load_event("cognitoDefineAuthChallengeEvent.json"))

    assert event.trigger_source == "DefineAuthChallenge_Authentication"

    # Verify properties
    assert event.request.user_attributes["email"] == "define-auth@mail.com"
    assert event.request.user_not_found is True
    session = event.request.session
    assert len(session) == 2
    assert session[0].challenge_name == "PASSWORD_VERIFIER"
    assert session[0].challenge_result is True
    assert session[0].challenge_metadata is None
    assert session[1].challenge_metadata == "CAPTCHA_CHALLENGE"
    assert event.request.client_metadata is None

    # Verify setters
    event.response.challenge_name = "CUSTOM_CHALLENGE"
    assert event.response.challenge_name == event["response"]["challengeName"]
    assert event.response.challenge_name == "CUSTOM_CHALLENGE"
    event.response.fail_authentication = True
    assert event.response.fail_authentication is True
    assert event.response.fail_authentication == event["response"]["failAuthentication"]
    event.response.issue_tokens = True
    assert event.response.issue_tokens is True
    assert event.response.issue_tokens == event["response"]["issueTokens"]


def test_create_auth_challenge_trigger_event():
    event = CreateAuthChallengeTriggerEvent(load_event("cognitoCreateAuthChallengeEvent.json"))

    assert event.trigger_source == "CreateAuthChallenge_Authentication"

    # Verify properties
    assert event.request.user_attributes["email"] == "create-auth@mail.com"
    assert event.request.user_not_found is False
    assert event.request.challenge_name == "PASSWORD_VERIFIER"
    session = event.request.session
    assert len(session) == 1
    assert session[0].challenge_name == "CUSTOM_CHALLENGE"
    assert session[0].challenge_metadata == "CAPTCHA_CHALLENGE"
    assert event.request.client_metadata is None

    # Verify setters
    event.response.public_challenge_parameters = {"test": "value"}
    assert event.response.public_challenge_parameters == event["response"]["publicChallengeParameters"]
    assert event.response.public_challenge_parameters["test"] == "value"
    event.response.private_challenge_parameters = {"private": "value"}
    assert event.response.private_challenge_parameters == event["response"]["privateChallengeParameters"]
    assert event.response.private_challenge_parameters["private"] == "value"
    event.response.challenge_metadata = "meta"
    assert event.response.challenge_metadata == event["response"]["challengeMetadata"]
    assert event.response.challenge_metadata == "meta"


def test_verify_auth_challenge_response_trigger_event():
    event = VerifyAuthChallengeResponseTriggerEvent(load_event("cognitoVerifyAuthChallengeResponseEvent.json"))

    assert event.trigger_source == "VerifyAuthChallengeResponse_Authentication"

    # Verify properties
    assert event.request.user_attributes["email"] == "verify-auth@mail.com"
    assert event.request.private_challenge_parameters["answer"] == "challengeAnswer"
    assert event.request.challenge_answer == "challengeAnswer"
    assert event.request.client_metadata is not None
    assert event.request.client_metadata["foo"] == "value"
    assert event.request.user_not_found is True

    # Verify setters
    event.response.answer_correct = True
    assert event.response.answer_correct == event["response"]["answerCorrect"]
    assert event.response.answer_correct is True


def test_connect_contact_flow_event_min():
    event = ConnectContactFlowEvent(load_event("connectContactFlowEventMin.json"))

    assert event.contact_data.attributes == {}
    assert event.contact_data.channel == ConnectContactFlowChannel.VOICE
    assert event.contact_data.contact_id == "5ca32fbd-8f92-46af-92a5-6b0f970f0efe"
    assert event.contact_data.customer_endpoint is None
    assert event.contact_data.initial_contact_id == "5ca32fbd-8f92-46af-92a5-6b0f970f0efe"
    assert event.contact_data.initiation_method == ConnectContactFlowInitiationMethod.API
    assert (
        event.contact_data.instance_arn
        == "arn:aws:connect:eu-central-1:123456789012:instance/9308c2a1-9bc6-4cea-8290-6c0b4a6d38fa"
    )
    assert event.contact_data.media_streams.customer.audio.start_fragment_number is None
    assert event.contact_data.media_streams.customer.audio.start_timestamp is None
    assert event.contact_data.media_streams.customer.audio.stream_arn is None
    assert event.contact_data.previous_contact_id == "5ca32fbd-8f92-46af-92a5-6b0f970f0efe"
    assert event.contact_data.queue is None
    assert event.contact_data.system_endpoint is None
    assert event.parameters == {}


def test_connect_contact_flow_event_all():
    event = ConnectContactFlowEvent(load_event("connectContactFlowEventAll.json"))

    assert event.contact_data.attributes == {"Language": "en-US"}
    assert event.contact_data.channel == ConnectContactFlowChannel.VOICE
    assert event.contact_data.contact_id == "5ca32fbd-8f92-46af-92a5-6b0f970f0efe"
    assert event.contact_data.customer_endpoint is not None
    assert event.contact_data.customer_endpoint.address == "+11234567890"
    assert event.contact_data.customer_endpoint.endpoint_type == ConnectContactFlowEndpointType.TELEPHONE_NUMBER
    assert event.contact_data.initial_contact_id == "5ca32fbd-8f92-46af-92a5-6b0f970f0efe"
    assert event.contact_data.initiation_method == ConnectContactFlowInitiationMethod.API
    assert (
        event.contact_data.instance_arn
        == "arn:aws:connect:eu-central-1:123456789012:instance/9308c2a1-9bc6-4cea-8290-6c0b4a6d38fa"
    )
    assert (
        event.contact_data.media_streams.customer.audio.start_fragment_number
        == "91343852333181432392682062622220590765191907586"
    )
    assert event.contact_data.media_streams.customer.audio.start_timestamp == "1565781909613"
    assert (
        event.contact_data.media_streams.customer.audio.stream_arn
        == "arn:aws:kinesisvideo:eu-central-1:123456789012:stream/"
        + "connect-contact-a3d73b84-ce0e-479a-a9dc-5637c9d30ac9/1565272947806"
    )
    assert event.contact_data.previous_contact_id == "5ca32fbd-8f92-46af-92a5-6b0f970f0efe"
    assert event.contact_data.queue is not None
    assert (
        event.contact_data.queue.arn
        == "arn:aws:connect:eu-central-1:123456789012:instance/9308c2a1-9bc6-4cea-8290-6c0b4a6d38fa/"
        + "queue/5cba7cbf-1ecb-4b6d-b8bd-fe91079b3fc8"
    )
    assert event.contact_data.queue.name == "QueueOne"
    assert event.contact_data.system_endpoint is not None
    assert event.contact_data.system_endpoint.address == "+11234567890"
    assert event.contact_data.system_endpoint.endpoint_type == ConnectContactFlowEndpointType.TELEPHONE_NUMBER
    assert event.parameters == {"ParameterOne": "One", "ParameterTwo": "Two"}


def test_dynamo_db_stream_trigger_event():
    event = DynamoDBStreamEvent(load_event("dynamoStreamEvent.json"))

    records = list(event.records)

    record = records[0]
    assert record.aws_region == "us-west-2"
    dynamodb = record.dynamodb
    assert dynamodb is not None
    assert dynamodb.approximate_creation_date_time is None
    keys = dynamodb.keys
    assert keys is not None
    id_key = keys["Id"]
    assert id_key.b_value is None
    assert id_key.bs_value is None
    assert id_key.bool_value is None
    assert id_key.list_value is None
    assert id_key.map_value is None
    assert id_key.n_value == "101"
    assert id_key.ns_value is None
    assert id_key.null_value is None
    assert id_key.s_value is None
    assert id_key.ss_value is None
    message_key = dynamodb.new_image["Message"]
    assert message_key is not None
    assert message_key.s_value == "New item!"
    assert dynamodb.old_image is None
    assert dynamodb.sequence_number == "111"
    assert dynamodb.size_bytes == 26
    assert dynamodb.stream_view_type == StreamViewType.NEW_AND_OLD_IMAGES
    assert record.event_id == "1"
    assert record.event_name is DynamoDBRecordEventName.INSERT
    assert record.event_source == "aws:dynamodb"
    assert record.event_source_arn == "eventsource_arn"
    assert record.event_version == "1.0"
    assert record.user_identity is None


def test_dynamo_attribute_value_list_value():
    example_attribute_value = {"L": [{"S": "Cookies"}, {"S": "Coffee"}, {"N": "3.14159"}]}
    attribute_value = AttributeValue(example_attribute_value)
    list_value = attribute_value.list_value
    assert list_value is not None
    item = list_value[0]
    assert item.s_value == "Cookies"


def test_dynamo_attribute_value_map_value():
    example_attribute_value = {"M": {"Name": {"S": "Joe"}, "Age": {"N": "35"}}}

    attribute_value = AttributeValue(example_attribute_value)

    map_value = attribute_value.map_value
    assert map_value is not None
    item = map_value["Name"]
    assert item.s_value == "Joe"


def test_event_bridge_event():
    event = EventBridgeEvent(load_event("eventBridgeEvent.json"))

    assert event.get_id == event["id"]
    assert event.version == event["version"]
    assert event.account == event["account"]
    assert event.time == event["time"]
    assert event.region == event["region"]
    assert event.resources == event["resources"]
    assert event.source == event["source"]
    assert event.detail_type == event["detail-type"]
    assert event.detail == event["detail"]
    assert event.replay_name == "replay_archive"


def test_s3_trigger_event():
    event = S3Event(load_event("s3Event.json"))
    records = list(event.records)
    assert len(records) == 1
    record = records[0]
    assert record.event_version == "2.1"
    assert record.event_source == "aws:s3"
    assert record.aws_region == "us-east-2"
    assert record.event_time == "2019-09-03T19:37:27.192Z"
    assert record.event_name == "ObjectCreated:Put"
    user_identity = record.user_identity
    assert user_identity.principal_id == "AWS:AIDAINPONIXQXHT3IKHL2"
    request_parameters = record.request_parameters
    assert request_parameters.source_ip_address == "205.255.255.255"
    assert record.response_elements["x-amz-request-id"] == "D82B88E5F771F645"
    s3 = record.s3
    assert s3.s3_schema_version == "1.0"
    assert s3.configuration_id == "828aa6fc-f7b5-4305-8584-487c791949c1"
    bucket = s3.bucket
    assert bucket.name == "lambda-artifacts-deafc19498e3f2df"
    assert bucket.owner_identity.principal_id == "A3I5XTEXAMAI3E"
    assert bucket.arn == "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df"
    assert s3.get_object.key == "b21b84d653bb07b05b1e6b33684dc11b"
    assert s3.get_object.size == 1305107
    assert s3.get_object.etag == "b21b84d653bb07b05b1e6b33684dc11b"
    assert s3.get_object.version_id is None
    assert s3.get_object.sequencer == "0C0F6F405D6ED209E1"
    assert record.glacier_event_data is None
    assert event.record.raw_event == event["Records"][0]
    assert event.bucket_name == "lambda-artifacts-deafc19498e3f2df"
    assert event.object_key == "b21b84d653bb07b05b1e6b33684dc11b"


def test_s3_key_unquote_plus():
    tricky_name = "foo name+value"
    event_dict = {"Records": [{"s3": {"object": {"key": quote_plus(tricky_name)}}}]}
    event = S3Event(event_dict)
    assert event.object_key == tricky_name


def test_s3_key_url_decoded_key():
    event = S3Event(load_event("s3EventDecodedKey.json"))
    assert event.object_key == event.record["s3"]["object"]["urlDecodedKey"]


def test_s3_glacier_event():
    example_event = {
        "Records": [
            {
                "glacierEventData": {
                    "restoreEventData": {
                        "lifecycleRestorationExpiryTime": "1970-01-01T00:01:00.000Z",
                        "lifecycleRestoreStorageClass": "standard",
                    }
                }
            }
        ]
    }
    event = S3Event(example_event)
    record = next(event.records)
    glacier_event_data = record.glacier_event_data
    assert glacier_event_data is not None
    assert glacier_event_data.restore_event_data.lifecycle_restoration_expiry_time == "1970-01-01T00:01:00.000Z"
    assert glacier_event_data.restore_event_data.lifecycle_restore_storage_class == "standard"


def test_s3_glacier_event_json():
    event = S3Event(load_event("s3EventGlacier.json"))
    glacier_event_data = event.record.glacier_event_data
    assert glacier_event_data is not None
    assert glacier_event_data.restore_event_data.lifecycle_restoration_expiry_time == "1970-01-01T00:01:00.000Z"
    assert glacier_event_data.restore_event_data.lifecycle_restore_storage_class == "standard"


def test_ses_trigger_event():
    event = SESEvent(load_event("sesEvent.json"))

    expected_address = "johndoe@example.com"
    records = list(event.records)
    record = records[0]
    assert record.event_source == "aws:ses"
    assert record.event_version == "1.0"
    mail = record.ses.mail
    assert mail.timestamp == "1970-01-01T00:00:00.000Z"
    assert mail.source == "janedoe@example.com"
    assert mail.message_id == "o3vrnil0e2ic28tr"
    assert mail.destination == [expected_address]
    assert mail.headers_truncated is False
    headers = list(mail.headers)
    assert len(headers) == 10
    assert headers[0].name == "Return-Path"
    assert headers[0].value == "<janedoe@example.com>"
    common_headers = mail.common_headers
    assert common_headers.return_path == "janedoe@example.com"
    assert common_headers.get_from == common_headers.raw_event["from"]
    assert common_headers.date == "Wed, 7 Oct 2015 12:34:56 -0700"
    assert common_headers.to == [expected_address]
    assert common_headers.message_id == "<0123456789example.com>"
    assert common_headers.subject == "Test Subject"
    receipt = record.ses.receipt
    assert receipt.timestamp == "1970-01-01T00:00:00.000Z"
    assert receipt.processing_time_millis == 574
    assert receipt.recipients == [expected_address]
    assert receipt.spam_verdict.status == "PASS"
    assert receipt.virus_verdict.status == "PASS"
    assert receipt.spf_verdict.status == "PASS"
    assert receipt.dmarc_verdict.status == "PASS"
    action = receipt.action
    assert action.get_type == action.raw_event["type"]
    assert action.function_arn == action.raw_event["functionArn"]
    assert action.invocation_type == action.raw_event["invocationType"]
    assert event.record.raw_event == event["Records"][0]
    assert event.mail.raw_event == event["Records"][0]["ses"]["mail"]
    assert event.receipt.raw_event == event["Records"][0]["ses"]["receipt"]


def test_sns_trigger_event():
    event = SNSEvent(load_event("snsEvent.json"))
    records = list(event.records)
    assert len(records) == 1
    record = records[0]
    assert record.event_version == "1.0"
    assert record.event_subscription_arn == "arn:aws:sns:us-east-2:123456789012:sns-la ..."
    assert record.event_source == "aws:sns"
    sns = record.sns
    assert sns.signature_version == "1"
    assert sns.timestamp == "2019-01-02T12:45:07.000Z"
    assert sns.signature == "tcc6faL2yUC6dgZdmrwh1Y4cGa/ebXEkAi6RibDsvpi+tE/1+82j...65r=="
    assert sns.signing_cert_url == "https://sns.us-east-2.amazonaws.com/SimpleNotification"
    assert sns.message_id == "95df01b4-ee98-5cb9-9903-4c221d41eb5e"
    assert sns.message == "Hello from SNS!"
    message_attributes = sns.message_attributes
    test_message_attribute = message_attributes["Test"]
    assert test_message_attribute.get_type == "String"
    assert test_message_attribute.value == "TestString"
    assert sns.get_type == "Notification"
    assert sns.unsubscribe_url == "https://sns.us-east-2.amazonaws.com/?Action=Unsubscribe"
    assert sns.topic_arn == "arn:aws:sns:us-east-2:123456789012:sns-lambda"
    assert sns.subject == "TestInvoke"
    assert event.record.raw_event == event["Records"][0]
    assert event.sns_message == "Hello from SNS!"


def test_seq_trigger_event():
    event = SQSEvent(load_event("sqsEvent.json"))

    records = list(event.records)
    record = records[0]
    attributes = record.attributes
    message_attributes = record.message_attributes
    test_attr = message_attributes["testAttr"]

    assert len(records) == 2
    assert record.message_id == "059f36b4-87a3-44ab-83d2-661975830a7d"
    assert record.receipt_handle == "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a..."
    assert record.body == "Test message."
    assert attributes.aws_trace_header is None
    assert attributes.approximate_receive_count == "1"
    assert attributes.sent_timestamp == "1545082649183"
    assert attributes.sender_id == "AIDAIENQZJOLO23YVJ4VO"
    assert attributes.approximate_first_receive_timestamp == "1545082649185"
    assert attributes.sequence_number is None
    assert attributes.message_group_id is None
    assert attributes.message_deduplication_id is None
    assert message_attributes["NotFound"] is None
    assert message_attributes.get("NotFound") is None
    assert test_attr.string_value == "100"
    assert test_attr.binary_value == "base64Str"
    assert test_attr.data_type == "Number"
    assert record.md5_of_body == "e4e68fb7bd0e697a0ae8f1bb342846b3"
    assert record.event_source == "aws:sqs"
    assert record.event_source_arn == "arn:aws:sqs:us-east-2:123456789012:my-queue"
    assert record.aws_region == "us-east-2"


def test_api_gateway_proxy_event():
    event = APIGatewayProxyEvent(load_event("apiGatewayProxyEvent.json"))

    assert event.version == event["version"]
    assert event.resource == event["resource"]
    assert event.path == event["path"]
    assert event.http_method == event["httpMethod"]
    assert event.headers == event["headers"]
    assert event.multi_value_headers == event["multiValueHeaders"]
    assert event.query_string_parameters == event["queryStringParameters"]
    assert event.multi_value_query_string_parameters == event["multiValueQueryStringParameters"]

    request_context = event.request_context
    assert request_context.account_id == event["requestContext"]["accountId"]
    assert request_context.api_id == event["requestContext"]["apiId"]

    authorizer = request_context.authorizer
    assert authorizer.claims is None
    assert authorizer.scopes is None

    assert request_context.domain_name == event["requestContext"]["domainName"]
    assert request_context.domain_prefix == event["requestContext"]["domainPrefix"]
    assert request_context.extended_request_id == event["requestContext"]["extendedRequestId"]
    assert request_context.http_method == event["requestContext"]["httpMethod"]

    identity = request_context.identity
    assert identity.access_key == event["requestContext"]["identity"]["accessKey"]
    assert identity.account_id == event["requestContext"]["identity"]["accountId"]
    assert identity.caller == event["requestContext"]["identity"]["caller"]
    assert (
        identity.cognito_authentication_provider == event["requestContext"]["identity"]["cognitoAuthenticationProvider"]
    )
    assert identity.cognito_authentication_type == event["requestContext"]["identity"]["cognitoAuthenticationType"]
    assert identity.cognito_identity_id == event["requestContext"]["identity"]["cognitoIdentityId"]
    assert identity.cognito_identity_pool_id == event["requestContext"]["identity"]["cognitoIdentityPoolId"]
    assert identity.principal_org_id == event["requestContext"]["identity"]["principalOrgId"]
    assert identity.source_ip == event["requestContext"]["identity"]["sourceIp"]
    assert identity.user == event["requestContext"]["identity"]["user"]
    assert identity.user_agent == event["requestContext"]["identity"]["userAgent"]
    assert identity.user_arn == event["requestContext"]["identity"]["userArn"]

    assert request_context.path == event["requestContext"]["path"]
    assert request_context.protocol == event["requestContext"]["protocol"]
    assert request_context.request_id == event["requestContext"]["requestId"]
    assert request_context.request_time == event["requestContext"]["requestTime"]
    assert request_context.request_time_epoch == event["requestContext"]["requestTimeEpoch"]
    assert request_context.resource_id == event["requestContext"]["resourceId"]
    assert request_context.resource_path == event["requestContext"]["resourcePath"]
    assert request_context.stage == event["requestContext"]["stage"]

    assert event.path_parameters == event["pathParameters"]
    assert event.stage_variables == event["stageVariables"]
    assert event.body == event["body"]
    assert event.is_base64_encoded == event["isBase64Encoded"]

    assert request_context.connected_at is None
    assert request_context.connection_id is None
    assert request_context.event_type is None
    assert request_context.message_direction is None
    assert request_context.message_id is None
    assert request_context.route_key is None
    assert identity.api_key is None
    assert identity.api_key_id is None


def test_api_gateway_proxy_v2_event():
    event = APIGatewayProxyEventV2(load_event("apiGatewayProxyV2Event.json"))

    assert event.version == event["version"]
    assert event.route_key == event["routeKey"]
    assert event.raw_path == event["rawPath"]
    assert event.raw_query_string == event["rawQueryString"]
    assert event.cookies == event["cookies"]
    assert event.cookies[0] == "cookie1"
    assert event.headers == event["headers"]
    assert event.query_string_parameters == event["queryStringParameters"]
    assert event.query_string_parameters["parameter2"] == "value"

    request_context = event.request_context
    assert request_context.account_id == event["requestContext"]["accountId"]
    assert request_context.api_id == event["requestContext"]["apiId"]
    assert request_context.authorizer.jwt_claim == event["requestContext"]["authorizer"]["jwt"]["claims"]
    assert request_context.authorizer.jwt_scopes == event["requestContext"]["authorizer"]["jwt"]["scopes"]
    assert request_context.domain_name == event["requestContext"]["domainName"]
    assert request_context.domain_prefix == event["requestContext"]["domainPrefix"]

    http = request_context.http
    assert http.method == "POST"
    assert http.path == "/my/path"
    assert http.protocol == "HTTP/1.1"
    assert http.source_ip == "IP"
    assert http.user_agent == "agent"

    assert request_context.request_id == event["requestContext"]["requestId"]
    assert request_context.route_key == event["requestContext"]["routeKey"]
    assert request_context.stage == event["requestContext"]["stage"]
    assert request_context.time == event["requestContext"]["time"]
    assert request_context.time_epoch == event["requestContext"]["timeEpoch"]

    assert event.body == event["body"]
    assert event.path_parameters == event["pathParameters"]
    assert event.is_base64_encoded == event["isBase64Encoded"]
    assert event.stage_variables == event["stageVariables"]


def test_api_gateway_proxy_v2_lambda_authorizer_event():
    event = APIGatewayProxyEventV2(load_event("apiGatewayProxyV2LambdaAuthorizerEvent.json"))

    request_context = event.request_context
    assert request_context is not None
    lambda_props = request_context.authorizer.get_lambda
    assert lambda_props is not None
    assert lambda_props["key"] == "value"


def test_api_gateway_proxy_v2_iam_event():
    event = APIGatewayProxyEventV2(load_event("apiGatewayProxyV2IamEvent.json"))

    iam = event.request_context.authorizer.iam
    assert iam is not None
    assert iam.access_key == "ARIA2ZJZYVUEREEIHAKY"
    assert iam.account_id == "1234567890"
    assert iam.caller_id == "AROA7ZJZYVRE7C3DUXHH6:CognitoIdentityCredentials"
    assert iam.cognito_amr == ["foo"]
    assert iam.cognito_identity_id == "us-east-1:3f291106-8703-466b-8f2b-3ecee1ca56ce"
    assert iam.cognito_identity_pool_id == "us-east-1:4f291106-8703-466b-8f2b-3ecee1ca56ce"
    assert iam.principal_org_id == "AwsOrgId"
    assert iam.user_arn == "arn:aws:iam::1234567890:user/Admin"
    assert iam.user_id == "AROA2ZJZYVRE7Y3TUXHH6"


def test_base_proxy_event_get_query_string_value():
    default_value = "default"
    set_value = "value"

    event = BaseProxyEvent({})
    value = event.get_query_string_value("test", default_value)
    assert value == default_value

    event._data["queryStringParameters"] = {"test": set_value}
    value = event.get_query_string_value("test", default_value)
    assert value == set_value

    value = event.get_query_string_value("unknown", default_value)
    assert value == default_value

    value = event.get_query_string_value("unknown")
    assert value is None


def test_base_proxy_event_get_header_value():
    default_value = "default"
    set_value = "value"

    event = BaseProxyEvent({"headers": {}})
    value = event.get_header_value("test", default_value)
    assert value == default_value

    event._data["headers"] = {"test": set_value}
    value = event.get_header_value("test", default_value)
    assert value == set_value

    # Verify that the default look is case insensitive
    value = event.get_header_value("Test")
    assert value == set_value

    value = event.get_header_value("unknown", default_value)
    assert value == default_value

    value = event.get_header_value("unknown")
    assert value is None


def test_base_proxy_event_get_header_value_case_insensitive():
    default_value = "default"
    set_value = "value"

    event = BaseProxyEvent({"headers": {}})

    event._data["headers"] = {"Test": set_value}
    value = event.get_header_value("test", case_sensitive=True)
    assert value is None

    value = event.get_header_value("test", default_value=default_value, case_sensitive=True)
    assert value == default_value

    value = event.get_header_value("Test", case_sensitive=True)
    assert value == set_value

    value = event.get_header_value("unknown", default_value, case_sensitive=True)
    assert value == default_value

    value = event.get_header_value("unknown", case_sensitive=True)
    assert value is None


def test_kinesis_stream_event():
    event = KinesisStreamEvent(load_event("kinesisStreamEvent.json"))

    records = list(event.records)
    assert len(records) == 2
    record = records[0]

    assert record.aws_region == "us-east-2"
    assert record.event_id == "shardId-000000000006:49590338271490256608559692538361571095921575989136588898"
    assert record.event_name == "aws:kinesis:record"
    assert record.event_source == "aws:kinesis"
    assert record.event_source_arn == "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream"
    assert record.event_version == "1.0"
    assert record.invoke_identity_arn == "arn:aws:iam::123456789012:role/lambda-role"

    kinesis = record.kinesis
    assert kinesis._data["kinesis"] == event["Records"][0]["kinesis"]

    assert kinesis.approximate_arrival_timestamp == 1545084650.987
    assert kinesis.data == event["Records"][0]["kinesis"]["data"]
    assert kinesis.kinesis_schema_version == "1.0"
    assert kinesis.partition_key == "1"
    assert kinesis.sequence_number == "49590338271490256608559692538361571095921575989136588898"

    assert kinesis.data_as_text() == "Hello, this is a test."


def test_kinesis_stream_event_json_data():
    json_value = {"test": "value"}
    data = base64.b64encode(bytes(json.dumps(json_value), "utf-8")).decode("utf-8")
    event = KinesisStreamEvent({"Records": [{"kinesis": {"data": data}}]})
    assert next(event.records).kinesis.data_as_json() == json_value


def test_alb_event():
    event = ALBEvent(load_event("albEvent.json"))
    assert event.request_context.elb_target_group_arn == event["requestContext"]["elb"]["targetGroupArn"]
    assert event.http_method == event["httpMethod"]
    assert event.path == event["path"]
    assert event.query_string_parameters == event["queryStringParameters"]
    assert event.headers == event["headers"]
    assert event.multi_value_query_string_parameters == event.get("multiValueQueryStringParameters")
    assert event.multi_value_headers == event.get("multiValueHeaders")
    assert event.body == event["body"]
    assert event.is_base64_encoded == event["isBase64Encoded"]


def test_appsync_resolver_event():
    event = AppSyncResolverEvent(load_event("appSyncResolverEvent.json"))

    assert event.type_name == "Merchant"
    assert event.field_name == "locations"
    assert event.arguments["name"] == "value"
    assert event.identity["claims"]["token_use"] == "id"
    assert event.source["name"] == "Value"
    assert event.get_header_value("X-amzn-trace-id") == "Root=1-60488877-0b0c4e6727ab2a1c545babd0"
    assert event.get_header_value("X-amzn-trace-id", case_sensitive=True) is None
    assert event.get_header_value("missing", default_value="Foo") == "Foo"
    assert event.prev_result == {}
    assert event.stash is None

    info = event.info
    assert info is not None
    assert isinstance(info, AppSyncResolverEventInfo)
    assert info.field_name == event["fieldName"]
    assert info.parent_type_name == event["typeName"]
    assert info.variables is None
    assert info.selection_set_list is None
    assert info.selection_set_graphql is None

    assert isinstance(event.identity, AppSyncIdentityCognito)
    identity: AppSyncIdentityCognito = event.identity
    assert identity.claims is not None
    assert identity.sub == "07920713-4526-4642-9c88-2953512de441"
    assert len(identity.source_ip) == 1
    assert identity.username == "mike"
    assert identity.default_auth_strategy == "ALLOW"
    assert identity.groups is None
    assert identity.issuer == identity["issuer"]


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
    event = AppSyncResolverEvent(load_event("appSyncDirectResolver.json"))

    assert event.source is None
    assert event.arguments["id"] == "my identifier"
    assert event.stash == {}
    assert event.prev_result is None
    assert isinstance(event.identity, AppSyncIdentityCognito)

    info = event.info
    assert info is not None
    assert isinstance(info, AppSyncResolverEventInfo)
    assert info.selection_set_list is not None
    assert info.selection_set_list == info["selectionSetList"]
    assert info.selection_set_graphql == info["selectionSetGraphQL"]
    assert info.parent_type_name == info["parentTypeName"]
    assert info.field_name == info["fieldName"]

    assert event.type_name == info.parent_type_name
    assert event.field_name == info.field_name


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


def test_s3_object_event_iam():
    event = S3ObjectLambdaEvent(load_event("s3ObjectEventIAMUser.json"))

    assert event.request_id == "1a5ed718-5f53-471d-b6fe-5cf62d88d02a"
    assert event.object_context is not None
    object_context = event.object_context
    assert object_context.input_s3_url == event["getObjectContext"]["inputS3Url"]
    assert object_context.output_route == event["getObjectContext"]["outputRoute"]
    assert object_context.output_token == event["getObjectContext"]["outputToken"]
    assert event.configuration is not None
    configuration = event.configuration
    assert configuration.access_point_arn == event["configuration"]["accessPointArn"]
    assert configuration.supporting_access_point_arn == event["configuration"]["supportingAccessPointArn"]
    assert configuration.payload == event["configuration"]["payload"]
    assert event.user_request is not None
    user_request = event.user_request
    assert user_request.url == event["userRequest"]["url"]
    assert user_request.headers == event["userRequest"]["headers"]
    assert user_request.get_header_value("Accept-Encoding") == "identity"
    assert event.user_identity is not None
    user_identity = event.user_identity
    assert user_identity.get_type == event["userIdentity"]["type"]
    assert user_identity.principal_id == event["userIdentity"]["principalId"]
    assert user_identity.arn == event["userIdentity"]["arn"]
    assert user_identity.account_id == event["userIdentity"]["accountId"]
    assert user_identity.access_key_id == event["userIdentity"]["accessKeyId"]
    assert user_identity.user_name == event["userIdentity"]["userName"]
    assert user_identity.session_context is None
    assert event.protocol_version == event["protocolVersion"]
    assert event.request_route == object_context.output_route
    assert event.request_token == object_context.output_token
    assert event.input_s3_url == object_context.input_s3_url


def test_s3_object_event_temp_credentials():
    event = S3ObjectLambdaEvent(load_event("s3ObjectEventTempCredentials.json"))

    assert event.request_id == "requestId"
    session_context = event.user_identity.session_context
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
