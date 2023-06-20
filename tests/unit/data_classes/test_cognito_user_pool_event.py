from secrets import compare_digest

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
from tests.functional.utils import load_event


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
    assert event.response.auto_confirm_user
    event.response.auto_verify_phone = True
    assert event.response.auto_verify_phone
    event.response.auto_verify_email = True
    assert event.response.auto_verify_email
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
    assert event.response.force_alias_creation
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
    claims_override_details = event.response.claims_override_details
    assert claims_override_details["groupOverrideDetails"]["groupsToOverride"] == expected_groups

    claims_override_details.set_group_configuration_iam_roles_to_override(["role"])
    assert claims_override_details.group_configuration.iam_roles_to_override == ["role"]
    assert event["response"]["claimsOverrideDetails"]["groupOverrideDetails"]["iamRolesToOverride"] == ["role"]

    claims_override_details.set_group_configuration_preferred_role("role_name")
    assert claims_override_details.group_configuration.preferred_role == "role_name"
    assert event["response"]["claimsOverrideDetails"]["groupOverrideDetails"]["preferredRole"] == "role_name"

    # Ensure that even if "claimsOverrideDetails" was explicitly set to None
    # accessing `event.response.claims_override_details` would set it to `{}`
    event["response"]["claimsOverrideDetails"] = None
    claims_override_details = event.response.claims_override_details
    assert claims_override_details._data == {}
    assert event["response"]["claimsOverrideDetails"] == {}
    claims_override_details.claims_to_suppress = ["email"]
    assert claims_override_details.claims_to_suppress[0] == "email"
    assert event["response"]["claimsOverrideDetails"]["claimsToSuppress"] == ["email"]


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
    assert event.response.fail_authentication
    assert event.response.fail_authentication == event["response"]["failAuthentication"]
    event.response.issue_tokens = True
    assert event.response.issue_tokens
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
    assert event.response.answer_correct
