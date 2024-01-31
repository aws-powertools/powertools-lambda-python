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
    raw_event = load_event("cognitoPreSignUpEvent.json")
    parsed_event = PreSignUpTriggerEvent(raw_event)

    # Verify BaseTriggerEvent properties
    assert parsed_event.version == raw_event["version"]
    assert parsed_event.trigger_source == raw_event["triggerSource"]
    assert parsed_event.region == raw_event["region"]
    assert parsed_event.user_pool_id == raw_event["userPoolId"]
    assert parsed_event.user_name == raw_event["userName"]
    caller_context = parsed_event.caller_context
    assert caller_context.aws_sdk_version == raw_event["callerContext"]["awsSdkVersion"]
    assert caller_context.client_id == raw_event["callerContext"]["clientId"]

    # Verify properties
    user_attributes = parsed_event.request.user_attributes
    assert user_attributes.get("email") == raw_event["request"]["userAttributes"]["email"]
    assert parsed_event.request.validation_data is None
    assert parsed_event.request.client_metadata is None

    # Verify setters
    parsed_event.response.auto_confirm_user = True
    assert parsed_event.response.auto_confirm_user
    parsed_event.response.auto_verify_phone = True
    assert parsed_event.response.auto_verify_phone
    parsed_event.response.auto_verify_email = True
    assert parsed_event.response.auto_verify_email
    assert parsed_event.response.auto_verify_email is True


def test_cognito_post_confirmation_trigger_event():
    raw_event = load_event("cognitoPostConfirmationEvent.json")
    parsed_event = PostConfirmationTriggerEvent(raw_event)

    assert parsed_event.trigger_source == raw_event["triggerSource"]

    user_attributes = parsed_event.request.user_attributes
    assert user_attributes.get("email") == raw_event["request"]["userAttributes"]["email"]
    assert parsed_event.request.client_metadata is None


def test_cognito_user_migration_trigger_event():
    raw_event = load_event("cognitoUserMigrationEvent.json")
    parsed_event = UserMigrationTriggerEvent(raw_event)

    assert parsed_event.trigger_source == raw_event["triggerSource"]

    assert compare_digest(parsed_event.request.password, raw_event["request"]["password"])
    assert parsed_event.request.validation_data is None
    assert parsed_event.request.client_metadata is None

    parsed_event.response.user_attributes = {"username": "username"}
    assert parsed_event.response.user_attributes == raw_event["response"]["userAttributes"]
    assert parsed_event.response.user_attributes == {"username": "username"}
    assert parsed_event.response.final_user_status is None
    assert parsed_event.response.message_action is None
    assert parsed_event.response.force_alias_creation is None
    assert parsed_event.response.desired_delivery_mediums is None

    parsed_event.response.final_user_status = "CONFIRMED"
    assert parsed_event.response.final_user_status == "CONFIRMED"
    parsed_event.response.message_action = "SUPPRESS"
    assert parsed_event.response.message_action == "SUPPRESS"
    parsed_event.response.force_alias_creation = True
    assert parsed_event.response.force_alias_creation
    parsed_event.response.desired_delivery_mediums = ["EMAIL"]
    assert parsed_event.response.desired_delivery_mediums == ["EMAIL"]


def test_cognito_custom_message_trigger_event():
    raw_event = load_event("cognitoCustomMessageEvent.json")
    parsed_event = CustomMessageTriggerEvent(raw_event)

    assert parsed_event.trigger_source == raw_event["triggerSource"]

    assert parsed_event.request.code_parameter == raw_event["request"]["codeParameter"]
    assert parsed_event.request.username_parameter == raw_event["request"]["usernameParameter"]
    assert parsed_event.request.user_attributes.get("phone_number_verified") is False
    assert parsed_event.request.client_metadata is None

    parsed_event.response.sms_message = "sms"
    assert parsed_event.response.sms_message == parsed_event["response"]["smsMessage"]
    parsed_event.response.email_message = "email"
    assert parsed_event.response.email_message == parsed_event["response"]["emailMessage"]
    parsed_event.response.email_subject = "subject"
    assert parsed_event.response.email_subject == parsed_event["response"]["emailSubject"]


def test_cognito_pre_authentication_trigger_event():
    raw_event = load_event("cognitoPreAuthenticationEvent.json")
    parsed_event = PreAuthenticationTriggerEvent(raw_event)

    assert parsed_event.trigger_source == raw_event["triggerSource"]

    assert parsed_event.request.user_not_found is None
    parsed_event["request"]["userNotFound"] = True
    assert parsed_event.request.user_not_found is True
    assert parsed_event.request.user_attributes.get("email") == raw_event["request"]["userAttributes"]["email"]
    assert parsed_event.request.validation_data is None


def test_cognito_post_authentication_trigger_event():
    raw_event = load_event("cognitoPostAuthenticationEvent.json")
    parsed_event = PostAuthenticationTriggerEvent(raw_event)

    assert parsed_event.trigger_source == raw_event["triggerSource"]

    assert parsed_event.request.new_device_used is True
    assert parsed_event.request.user_attributes.get("email") == raw_event["request"]["userAttributes"]["email"]
    assert parsed_event.request.client_metadata is None


def test_cognito_pre_token_generation_trigger_event():
    raw_event = load_event("cognitoPreTokenGenerationEvent.json")
    parsed_event = PreTokenGenerationTriggerEvent(raw_event)

    assert parsed_event.trigger_source == raw_event["triggerSource"]

    group_configuration = parsed_event.request.group_configuration
    assert group_configuration.groups_to_override == []
    assert group_configuration.iam_roles_to_override == []
    assert group_configuration.preferred_role is None
    assert parsed_event.request.user_attributes.get("email") == raw_event["request"]["userAttributes"]["email"]
    assert parsed_event.request.client_metadata is None

    parsed_event["request"]["groupConfiguration"]["preferredRole"] = "temp"
    group_configuration = parsed_event.request.group_configuration
    assert group_configuration.preferred_role == "temp"

    assert parsed_event["response"].get("claimsOverrideDetails") is None
    claims_override_details = parsed_event.response.claims_override_details
    assert parsed_event["response"]["claimsOverrideDetails"] == {}

    assert claims_override_details.claims_to_add_or_override is None
    assert claims_override_details.claims_to_suppress is None
    assert claims_override_details.group_configuration is None

    claims_override_details.group_configuration = {}
    assert claims_override_details.group_configuration._data == {}
    assert parsed_event["response"]["claimsOverrideDetails"]["groupOverrideDetails"] == {}

    expected_claims = {"test": "value"}
    claims_override_details.claims_to_add_or_override = expected_claims
    assert claims_override_details.claims_to_add_or_override["test"] == "value"
    assert parsed_event["response"]["claimsOverrideDetails"]["claimsToAddOrOverride"] == expected_claims

    claims_override_details.claims_to_suppress = ["email"]
    assert claims_override_details.claims_to_suppress[0] == "email"
    assert parsed_event["response"]["claimsOverrideDetails"]["claimsToSuppress"] == ["email"]

    expected_groups = ["group-A", "group-B"]
    claims_override_details.set_group_configuration_groups_to_override(expected_groups)
    assert claims_override_details.group_configuration.groups_to_override == expected_groups
    assert (
        parsed_event["response"]["claimsOverrideDetails"]["groupOverrideDetails"]["groupsToOverride"] == expected_groups
    )
    claims_override_details = parsed_event.response.claims_override_details
    assert claims_override_details["groupOverrideDetails"]["groupsToOverride"] == expected_groups

    claims_override_details.set_group_configuration_iam_roles_to_override(["role"])
    assert claims_override_details.group_configuration.iam_roles_to_override == ["role"]
    assert parsed_event["response"]["claimsOverrideDetails"]["groupOverrideDetails"]["iamRolesToOverride"] == ["role"]

    claims_override_details.set_group_configuration_preferred_role("role_name")
    assert claims_override_details.group_configuration.preferred_role == "role_name"
    assert parsed_event["response"]["claimsOverrideDetails"]["groupOverrideDetails"]["preferredRole"] == "role_name"

    # Ensure that even if "claimsOverrideDetails" was explicitly set to None
    # accessing `event.response.claims_override_details` would set it to `{}`
    parsed_event["response"]["claimsOverrideDetails"] = None
    claims_override_details = parsed_event.response.claims_override_details
    assert claims_override_details._data == {}
    assert parsed_event["response"]["claimsOverrideDetails"] == {}
    claims_override_details.claims_to_suppress = ["email"]
    assert claims_override_details.claims_to_suppress[0] == "email"
    assert parsed_event["response"]["claimsOverrideDetails"]["claimsToSuppress"] == ["email"]


def test_cognito_define_auth_challenge_trigger_event():
    raw_event = load_event("cognitoDefineAuthChallengeEvent.json")
    parsed_event = DefineAuthChallengeTriggerEvent(raw_event)

    assert parsed_event.trigger_source == raw_event["triggerSource"]

    # Verify properties
    assert parsed_event.request.user_attributes.get("email") == raw_event["request"]["userAttributes"]["email"]
    assert parsed_event.request.user_not_found is True
    session = parsed_event.request.session
    assert len(session) == 2
    assert session[0].challenge_name == raw_event["request"]["session"][0]["challengeName"]
    assert session[0].challenge_result is True
    assert session[0].challenge_metadata is None
    assert session[1].challenge_metadata == raw_event["request"]["session"][1]["challengeMetadata"]
    assert parsed_event.request.client_metadata is None

    # Verify setters
    parsed_event.response.challenge_name = "CUSTOM_CHALLENGE"
    assert parsed_event.response.challenge_name == parsed_event["response"]["challengeName"]
    assert parsed_event.response.challenge_name == "CUSTOM_CHALLENGE"
    parsed_event.response.fail_authentication = True
    assert parsed_event.response.fail_authentication
    assert parsed_event.response.fail_authentication == parsed_event["response"]["failAuthentication"]
    parsed_event.response.issue_tokens = True
    assert parsed_event.response.issue_tokens
    assert parsed_event.response.issue_tokens == parsed_event["response"]["issueTokens"]


def test_create_auth_challenge_trigger_event():
    raw_event = load_event("cognitoCreateAuthChallengeEvent.json")
    parsed_event = CreateAuthChallengeTriggerEvent(raw_event)

    assert parsed_event.trigger_source == raw_event["triggerSource"]

    # Verify properties
    assert parsed_event.request.user_attributes.get("email") == raw_event["request"]["userAttributes"]["email"]
    assert parsed_event.request.user_not_found is False
    assert parsed_event.request.challenge_name == raw_event["request"]["challengeName"]
    session = parsed_event.request.session
    assert len(session) == 1
    assert session[0].challenge_name == raw_event["request"]["session"][0]["challengeName"]
    assert session[0].challenge_metadata == raw_event["request"]["session"][0]["challengeMetadata"]
    assert parsed_event.request.client_metadata is None

    # Verify setters
    parsed_event.response.public_challenge_parameters = {"test": "value"}
    assert parsed_event.response.public_challenge_parameters == parsed_event["response"]["publicChallengeParameters"]
    assert parsed_event.response.public_challenge_parameters["test"] == "value"
    parsed_event.response.private_challenge_parameters = {"private": "value"}
    assert parsed_event.response.private_challenge_parameters == parsed_event["response"]["privateChallengeParameters"]
    assert parsed_event.response.private_challenge_parameters["private"] == "value"
    parsed_event.response.challenge_metadata = "meta"
    assert parsed_event.response.challenge_metadata == parsed_event["response"]["challengeMetadata"]
    assert parsed_event.response.challenge_metadata == "meta"


def test_verify_auth_challenge_response_trigger_event():
    raw_event = load_event("cognitoVerifyAuthChallengeResponseEvent.json")
    parsed_event = VerifyAuthChallengeResponseTriggerEvent(raw_event)

    assert parsed_event.trigger_source == raw_event["triggerSource"]

    # Verify properties
    assert parsed_event.request.user_attributes.get("email") == raw_event["request"]["userAttributes"]["email"]
    assert (
        parsed_event.request.private_challenge_parameters.get("answer")
        == raw_event["request"]["privateChallengeParameters"]["answer"]
    )
    assert parsed_event.request.challenge_answer == raw_event["request"]["challengeAnswer"]
    assert parsed_event.request.client_metadata is not None
    assert parsed_event.request.client_metadata.get("foo") == raw_event["request"]["clientMetadata"]["foo"]
    assert parsed_event.request.user_not_found is True

    # Verify setters
    parsed_event.response.answer_correct = True
    assert parsed_event.response.answer_correct == parsed_event["response"]["answerCorrect"]
    assert parsed_event.response.answer_correct
