from typing import Any, Dict, List, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class CallerContext(DictWrapper):
    @property
    def aws_sdk_version(self) -> str:
        """The AWS SDK version number."""
        return self["callerContext"]["awsSdkVersion"]

    @property
    def client_id(self) -> str:
        """The ID of the client associated with the user pool."""
        return self["callerContext"]["clientId"]


class BaseTriggerEvent(DictWrapper):
    """Common attributes shared by all User Pool Lambda Trigger Events

    Documentation:
    -------------
    https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools-working-with-aws-lambda-triggers.html
    """

    @property
    def version(self) -> str:
        """The version number of your Lambda function."""
        return self["version"]

    @property
    def region(self) -> str:
        """The AWS Region, as an AWSRegion instance."""
        return self["region"]

    @property
    def user_pool_id(self) -> str:
        """The user pool ID for the user pool."""
        return self["userPoolId"]

    @property
    def trigger_source(self) -> str:
        """The name of the event that triggered the Lambda function."""
        return self["triggerSource"]

    @property
    def user_name(self) -> str:
        """The username of the current user."""
        return self["userName"]

    @property
    def caller_context(self) -> CallerContext:
        """The caller context"""
        return CallerContext(self._data)


class PreSignUpTriggerEventRequest(DictWrapper):
    @property
    def user_attributes(self) -> Dict[str, str]:
        """One or more name-value pairs representing user attributes. The attribute names are the keys."""
        return self["request"]["userAttributes"]

    @property
    def validation_data(self) -> Optional[Dict[str, str]]:
        """One or more name-value pairs containing the validation data in the request to register a user."""
        return self["request"].get("validationData")

    @property
    def client_metadata(self) -> Optional[Dict[str, str]]:
        """One or more key-value pairs that you can provide as custom input to the Lambda function
        that you specify for the pre sign-up trigger."""
        return self["request"].get("clientMetadata")


class PreSignUpTriggerEventResponse(DictWrapper):
    @property
    def auto_confirm_user(self) -> bool:
        return bool(self["response"]["autoConfirmUser"])

    @auto_confirm_user.setter
    def auto_confirm_user(self, value: bool):
        """Set to true to auto-confirm the user, or false otherwise."""
        self["response"]["autoConfirmUser"] = value

    @property
    def auto_verify_email(self) -> bool:
        return bool(self["response"]["autoVerifyEmail"])

    @auto_verify_email.setter
    def auto_verify_email(self, value: bool):
        """Set to true to set as verified the email of a user who is signing up, or false otherwise."""
        self["response"]["autoVerifyEmail"] = value

    @property
    def auto_verify_phone(self) -> bool:
        return bool(self["response"]["autoVerifyPhone"])

    @auto_verify_phone.setter
    def auto_verify_phone(self, value: bool):
        """Set to true to set as verified the phone number of a user who is signing up, or false otherwise."""
        self["response"]["autoVerifyPhone"] = value


class PreSignUpTriggerEvent(BaseTriggerEvent):
    """Pre Sign-up Lambda Trigger

    Notes:
    ----
    `triggerSource` can be one of the following:

    - `PreSignUp_SignUp` Pre sign-up.
    - `PreSignUp_AdminCreateUser` Pre sign-up when an admin creates a new user.
    - `PreSignUp_ExternalProvider` Pre sign-up with external provider

    Documentation:
    -------------
    - https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-sign-up.html
    """

    @property
    def request(self) -> PreSignUpTriggerEventRequest:
        return PreSignUpTriggerEventRequest(self._data)

    @property
    def response(self) -> PreSignUpTriggerEventResponse:
        return PreSignUpTriggerEventResponse(self._data)


class PostConfirmationTriggerEventRequest(DictWrapper):
    @property
    def user_attributes(self) -> Dict[str, str]:
        """One or more name-value pairs representing user attributes. The attribute names are the keys."""
        return self["request"]["userAttributes"]

    @property
    def client_metadata(self) -> Optional[Dict[str, str]]:
        """One or more key-value pairs that you can provide as custom input to the Lambda function
        that you specify for the post confirmation trigger."""
        return self["request"].get("clientMetadata")


class PostConfirmationTriggerEvent(BaseTriggerEvent):
    """Post Confirmation Lambda Trigger

    Notes:
    ----
    `triggerSource` can be one of the following:

    - `PostConfirmation_ConfirmSignUp` Post sign-up confirmation.
    - `PostConfirmation_ConfirmForgotPassword` Post Forgot Password confirmation.

    Documentation:
    -------------
    - https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-post-confirmation.html
    """

    @property
    def request(self) -> PostConfirmationTriggerEventRequest:
        return PostConfirmationTriggerEventRequest(self._data)


class UserMigrationTriggerEventRequest(DictWrapper):
    @property
    def password(self) -> str:
        return self["request"]["password"]

    @property
    def validation_data(self) -> Optional[Dict[str, str]]:
        """One or more name-value pairs containing the validation data in the request to register a user."""
        return self["request"].get("validationData")

    @property
    def client_metadata(self) -> Optional[Dict[str, str]]:
        """One or more key-value pairs that you can provide as custom input to the Lambda function
        that you specify for the pre sign-up trigger."""
        return self["request"].get("clientMetadata")


class UserMigrationTriggerEventResponse(DictWrapper):
    @property
    def user_attributes(self) -> Dict[str, str]:
        return self["response"]["userAttributes"]

    @user_attributes.setter
    def user_attributes(self, value: Dict[str, str]):
        """It must contain one or more name-value pairs representing user attributes to be stored in the
        user profile in your user pool. You can include both standard and custom user attributes.
        Custom attributes require the custom: prefix to distinguish them from standard attributes."""
        self["response"]["userAttributes"] = value

    @property
    def final_user_status(self) -> Optional[str]:
        return self["response"].get("finalUserStatus")

    @final_user_status.setter
    def final_user_status(self, value: str):
        """During sign-in, this attribute can be set to CONFIRMED, or not set, to auto-confirm your users and
        allow them to sign-in with their previous passwords. This is the simplest experience for the user.

        If this attribute is set to RESET_REQUIRED, the user is required to change his or her password immediately
        after migration at the time of sign-in, and your client app needs to handle the PasswordResetRequiredException
        during the authentication flow."""
        self["response"]["finalUserStatus"] = value

    @property
    def message_action(self) -> Optional[str]:
        return self["response"].get("messageAction")

    @message_action.setter
    def message_action(self, value: str):
        """This attribute can be set to "SUPPRESS" to suppress the welcome message usually sent by
        Amazon Cognito to new users. If this attribute is not returned, the welcome message will be sent."""
        self["response"]["messageAction"] = value

    @property
    def desired_delivery_mediums(self) -> Optional[List[str]]:
        return self["response"].get("desiredDeliveryMediums")

    @desired_delivery_mediums.setter
    def desired_delivery_mediums(self, value: List[str]):
        """This attribute can be set to "EMAIL" to send the welcome message by email, or "SMS" to send the
        welcome message by SMS. If this attribute is not returned, the welcome message will be sent by SMS."""
        self["response"]["desiredDeliveryMediums"] = value

    @property
    def force_alias_creation(self) -> Optional[bool]:
        return self["response"].get("forceAliasCreation")

    @force_alias_creation.setter
    def force_alias_creation(self, value: bool):
        """If this parameter is set to "true" and the phone number or email address specified in the UserAttributes
        parameter already exists as an alias with a different user, the API call will migrate the alias from the
        previous user to the newly created user. The previous user will no longer be able to log in using that alias.

        If this attribute is set to "false" and the alias exists, the user will not be migrated, and an error is
        returned to the client app.

        If this attribute is not returned, it is assumed to be "false".
        """
        self["response"]["forceAliasCreation"] = value


class UserMigrationTriggerEvent(BaseTriggerEvent):
    """Migrate User Lambda Trigger

    Notes:
    ----
    `triggerSource` can be one of the following:

    - `UserMigration_Authentication` User migration at the time of sign in.
    - `UserMigration_ForgotPassword` User migration during forgot-password flow.

    Documentation:
    -------------
    - https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-migrate-user.html
    """

    @property
    def request(self) -> UserMigrationTriggerEventRequest:
        return UserMigrationTriggerEventRequest(self._data)

    @property
    def response(self) -> UserMigrationTriggerEventResponse:
        return UserMigrationTriggerEventResponse(self._data)


class CustomMessageTriggerEventRequest(DictWrapper):
    @property
    def code_parameter(self) -> str:
        """A string for you to use as the placeholder for the verification code in the custom message."""
        return self["request"]["codeParameter"]

    @property
    def username_parameter(self) -> str:
        """The username parameter. It is a required request parameter for the admin create user flow."""
        return self["request"]["usernameParameter"]

    @property
    def user_attributes(self) -> Dict[str, str]:
        """One or more name-value pairs representing user attributes. The attribute names are the keys."""
        return self["request"]["userAttributes"]

    @property
    def client_metadata(self) -> Optional[Dict[str, str]]:
        """One or more key-value pairs that you can provide as custom input to the Lambda function
        that you specify for the pre sign-up trigger."""
        return self["request"].get("clientMetadata")


class CustomMessageTriggerEventResponse(DictWrapper):
    @property
    def sms_message(self) -> str:
        return self["response"]["smsMessage"]

    @sms_message.setter
    def sms_message(self, value: str):
        """The custom SMS message to be sent to your users.
        Must include the codeParameter value received in the request."""
        self["response"]["smsMessage"] = value

    @property
    def email_message(self) -> str:
        return self["response"]["emailMessage"]

    @email_message.setter
    def email_message(self, value: str):
        """The custom email message to be sent to your users.
        Must include the codeParameter value received in the request."""
        self["response"]["emailMessage"] = value

    @property
    def email_subject(self) -> str:
        return self["response"]["emailSubject"]

    @email_subject.setter
    def email_subject(self, value: str):
        """The subject line for the custom message."""
        self["response"]["emailSubject"] = value


class CustomMessageTriggerEvent(BaseTriggerEvent):
    """Custom Message Lambda Trigger

    Notes:
    ----
    `triggerSource` can be one of the following:

    - `CustomMessage_SignUp` To send the confirmation code post sign-up.
    - `CustomMessage_AdminCreateUser` To send the temporary password to a new user.
    - `CustomMessage_ResendCode` To resend the confirmation code to an existing user.
    - `CustomMessage_ForgotPassword` To send the confirmation code for Forgot Password request.
    - `CustomMessage_UpdateUserAttribute` When a user's email or phone number is changed, this trigger sends a
       verification code automatically to the user. Cannot be used for other attributes.
    - `CustomMessage_VerifyUserAttribute`  This trigger sends a verification code to the user when they manually
       request it for a new email or phone number.
    - `CustomMessage_Authentication` To send MFA code during authentication.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-custom-message.html
    """

    @property
    def request(self) -> CustomMessageTriggerEventRequest:
        return CustomMessageTriggerEventRequest(self._data)

    @property
    def response(self) -> CustomMessageTriggerEventResponse:
        return CustomMessageTriggerEventResponse(self._data)


class PreAuthenticationTriggerEventRequest(DictWrapper):
    @property
    def user_not_found(self) -> Optional[bool]:
        """This boolean is populated when PreventUserExistenceErrors is set to ENABLED for your User Pool client."""
        return self["request"].get("userNotFound")

    @property
    def user_attributes(self) -> Dict[str, str]:
        """One or more name-value pairs representing user attributes."""
        return self["request"]["userAttributes"]

    @property
    def validation_data(self) -> Optional[Dict[str, str]]:
        """One or more key-value pairs containing the validation data in the user's sign-in request."""
        return self["request"].get("validationData")


class PreAuthenticationTriggerEvent(BaseTriggerEvent):
    """Pre Authentication Lambda Trigger

    Amazon Cognito invokes this trigger when a user attempts to sign in, allowing custom validation
    to accept or deny the authentication request.

    Notes:
    ----
    `triggerSource` can be one of the following:

    - `PreAuthentication_Authentication` Pre authentication.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-authentication.html
    """

    @property
    def request(self) -> PreAuthenticationTriggerEventRequest:
        """Pre Authentication Request Parameters"""
        return PreAuthenticationTriggerEventRequest(self._data)


class PostAuthenticationTriggerEventRequest(DictWrapper):
    @property
    def new_device_used(self) -> bool:
        """This flag indicates if the user has signed in on a new device.
        It is set only if the remembered devices value of the user pool is set to `Always` or User `Opt-In`."""
        return self["request"]["newDeviceUsed"]

    @property
    def user_attributes(self) -> Dict[str, str]:
        """One or more name-value pairs representing user attributes."""
        return self["request"]["userAttributes"]

    @property
    def client_metadata(self) -> Optional[Dict[str, str]]:
        """One or more key-value pairs that you can provide as custom input to the Lambda function
        that you specify for the post authentication trigger."""
        return self["request"].get("clientMetadata")


class PostAuthenticationTriggerEvent(BaseTriggerEvent):
    """Post Authentication Lambda Trigger

    Amazon Cognito invokes this trigger after signing in a user, allowing you to add custom logic
    after authentication.

    Notes:
    ----
    `triggerSource` can be one of the following:

    - `PostAuthentication_Authentication` Post authentication.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-post-authentication.html
    """

    @property
    def request(self) -> PostAuthenticationTriggerEventRequest:
        """Post Authentication Request Parameters"""
        return PostAuthenticationTriggerEventRequest(self._data)


class GroupOverrideDetails(DictWrapper):
    @property
    def groups_to_override(self) -> Optional[List[str]]:
        """A list of the group names that are associated with the user that the identity token is issued for."""
        return self.get("groupsToOverride")

    @property
    def iam_roles_to_override(self) -> Optional[List[str]]:
        """A list of the current IAM roles associated with these groups."""
        return self.get("iamRolesToOverride")

    @property
    def preferred_role(self) -> Optional[str]:
        """A string indicating the preferred IAM role."""
        return self.get("preferredRole")


class PreTokenGenerationTriggerEventRequest(DictWrapper):
    @property
    def group_configuration(self) -> GroupOverrideDetails:
        """The input object containing the current group configuration"""
        return GroupOverrideDetails(self["request"]["groupConfiguration"])

    @property
    def user_attributes(self) -> Dict[str, str]:
        """One or more name-value pairs representing user attributes."""
        return self["request"]["userAttributes"]

    @property
    def client_metadata(self) -> Optional[Dict[str, str]]:
        """One or more key-value pairs that you can provide as custom input to the Lambda function
        that you specify for the pre token generation trigger."""
        return self["request"].get("clientMetadata")


class ClaimsOverrideDetails(DictWrapper):
    @property
    def claims_to_add_or_override(self) -> Optional[Dict[str, str]]:
        return self.get("claimsToAddOrOverride")

    @claims_to_add_or_override.setter
    def claims_to_add_or_override(self, value: Dict[str, str]):
        """A map of one or more key-value pairs of claims to add or override.
        For group related claims, use groupOverrideDetails instead."""
        self._data["claimsToAddOrOverride"] = value

    @property
    def claims_to_suppress(self) -> Optional[List[str]]:
        return self.get("claimsToSuppress")

    @claims_to_suppress.setter
    def claims_to_suppress(self, value: List[str]):
        """A list that contains claims to be suppressed from the identity token."""
        self._data["claimsToSuppress"] = value

    @property
    def group_configuration(self) -> Optional[GroupOverrideDetails]:
        group_override_details = self.get("groupOverrideDetails")
        return None if group_override_details is None else GroupOverrideDetails(group_override_details)

    @group_configuration.setter
    def group_configuration(self, value: Dict[str, Any]):
        """The output object containing the current group configuration.

        It includes groupsToOverride, iamRolesToOverride, and preferredRole.

        The groupOverrideDetails object is replaced with the one you provide. If you provide an empty or null
        object in the response, then the groups are suppressed. To leave the existing group configuration
        as is, copy the value of the request's groupConfiguration object to the groupOverrideDetails object
        in the response, and pass it back to the service.
        """
        self._data["groupOverrideDetails"] = value

    def set_group_configuration_groups_to_override(self, value: List[str]):
        """A list of the group names that are associated with the user that the identity token is issued for."""
        self._data.setdefault("groupOverrideDetails", {})
        self["groupOverrideDetails"]["groupsToOverride"] = value

    def set_group_configuration_iam_roles_to_override(self, value: List[str]):
        """A list of the current IAM roles associated with these groups."""
        self._data.setdefault("groupOverrideDetails", {})
        self["groupOverrideDetails"]["iamRolesToOverride"] = value

    def set_group_configuration_preferred_role(self, value: str):
        """A string indicating the preferred IAM role."""
        self._data.setdefault("groupOverrideDetails", {})
        self["groupOverrideDetails"]["preferredRole"] = value


class PreTokenGenerationTriggerEventResponse(DictWrapper):
    @property
    def claims_override_details(self) -> ClaimsOverrideDetails:
        # Ensure we have a `claimsOverrideDetails` element and is not set to None
        if self._data["response"].get("claimsOverrideDetails") is None:
            self._data["response"]["claimsOverrideDetails"] = {}
        return ClaimsOverrideDetails(self._data["response"]["claimsOverrideDetails"])


class PreTokenGenerationTriggerEvent(BaseTriggerEvent):
    """Pre Token Generation Lambda Trigger

    Amazon Cognito invokes this trigger before token generation allowing you to customize identity token claims.

    Notes:
    ----
    `triggerSource` can be one of the following:

    - `TokenGeneration_HostedAuth` Called during authentication from the Amazon Cognito hosted UI sign-in page.
    - `TokenGeneration_Authentication` Called after user authentication flows have completed.
    - `TokenGeneration_NewPasswordChallenge` Called after the user is created by an admin. This flow is invoked
       when the user has to change a temporary password.
    - `TokenGeneration_AuthenticateDevice` Called at the end of the authentication of a user device.
    - `TokenGeneration_RefreshTokens` Called when a user tries to refresh the identity and access tokens.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html
    """

    @property
    def request(self) -> PreTokenGenerationTriggerEventRequest:
        """Pre Token Generation Request Parameters"""
        return PreTokenGenerationTriggerEventRequest(self._data)

    @property
    def response(self) -> PreTokenGenerationTriggerEventResponse:
        """Pre Token Generation Response Parameters"""
        return PreTokenGenerationTriggerEventResponse(self._data)


class ChallengeResult(DictWrapper):
    @property
    def challenge_name(self) -> str:
        """The challenge type.

        One of: CUSTOM_CHALLENGE, SRP_A, PASSWORD_VERIFIER, SMS_MFA, DEVICE_SRP_AUTH,
        DEVICE_PASSWORD_VERIFIER, or ADMIN_NO_SRP_AUTH."""
        return self["challengeName"]

    @property
    def challenge_result(self) -> bool:
        """Set to true if the user successfully completed the challenge, or false otherwise."""
        return bool(self["challengeResult"])

    @property
    def challenge_metadata(self) -> Optional[str]:
        """Your name for the custom challenge. Used only if challengeName is CUSTOM_CHALLENGE."""
        return self.get("challengeMetadata")


class DefineAuthChallengeTriggerEventRequest(DictWrapper):
    @property
    def user_attributes(self) -> Dict[str, str]:
        """One or more name-value pairs representing user attributes. The attribute names are the keys."""
        return self["request"]["userAttributes"]

    @property
    def user_not_found(self) -> Optional[bool]:
        """A Boolean that is populated when PreventUserExistenceErrors is set to ENABLED for your user pool client.
        A value of true means that the user id (user name, email address, etc.) did not match any existing users."""
        return self["request"].get("userNotFound")

    @property
    def session(self) -> List[ChallengeResult]:
        """An array of ChallengeResult elements, each of which contains the following elements:"""
        return [ChallengeResult(result) for result in self["request"]["session"]]

    @property
    def client_metadata(self) -> Optional[Dict[str, str]]:
        """One or more key-value pairs that you can provide as custom input to the Lambda function that you specify
        for the define auth challenge trigger."""
        return self["request"].get("clientMetadata")


class DefineAuthChallengeTriggerEventResponse(DictWrapper):
    @property
    def challenge_name(self) -> str:
        return self["response"]["challengeName"]

    @challenge_name.setter
    def challenge_name(self, value: str):
        """A string containing the name of the next challenge.
        If you want to present a new challenge to your user, specify the challenge name here."""
        self["response"]["challengeName"] = value

    @property
    def fail_authentication(self) -> bool:
        return bool(self["response"]["failAuthentication"])

    @fail_authentication.setter
    def fail_authentication(self, value: bool):
        """Set to true if you want to terminate the current authentication process, or false otherwise."""
        self["response"]["failAuthentication"] = value

    @property
    def issue_tokens(self) -> bool:
        return bool(self["response"]["issueTokens"])

    @issue_tokens.setter
    def issue_tokens(self, value: bool):
        """Set to true if you determine that the user has been sufficiently authenticated by
        completing the challenges, or false otherwise."""
        self["response"]["issueTokens"] = value


class DefineAuthChallengeTriggerEvent(BaseTriggerEvent):
    """Define Auth Challenge Lambda Trigger

    Amazon Cognito invokes this trigger to initiate the custom authentication flow.

    Notes:
    ----
    `triggerSource` can be one of the following:

    - `DefineAuthChallenge_Authentication` Define Auth Challenge.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-define-auth-challenge.html
    """

    @property
    def request(self) -> DefineAuthChallengeTriggerEventRequest:
        """Define Auth Challenge Request Parameters"""
        return DefineAuthChallengeTriggerEventRequest(self._data)

    @property
    def response(self) -> DefineAuthChallengeTriggerEventResponse:
        """Define Auth Challenge Response Parameters"""
        return DefineAuthChallengeTriggerEventResponse(self._data)


class CreateAuthChallengeTriggerEventRequest(DictWrapper):
    @property
    def user_attributes(self) -> Dict[str, str]:
        """One or more name-value pairs representing user attributes. The attribute names are the keys."""
        return self["request"]["userAttributes"]

    @property
    def user_not_found(self) -> Optional[bool]:
        """This boolean is populated when PreventUserExistenceErrors is set to ENABLED for your User Pool client."""
        return self["request"].get("userNotFound")

    @property
    def challenge_name(self) -> str:
        """The name of the new challenge."""
        return self["request"]["challengeName"]

    @property
    def session(self) -> List[ChallengeResult]:
        """An array of ChallengeResult elements, each of which contains the following elements:"""
        return [ChallengeResult(result) for result in self["request"]["session"]]

    @property
    def client_metadata(self) -> Optional[Dict[str, str]]:
        """One or more key-value pairs that you can provide as custom input to the Lambda function that you
        specify for the create auth challenge trigger.."""
        return self["request"].get("clientMetadata")


class CreateAuthChallengeTriggerEventResponse(DictWrapper):
    @property
    def public_challenge_parameters(self) -> Dict[str, str]:
        return self["response"]["publicChallengeParameters"]

    @public_challenge_parameters.setter
    def public_challenge_parameters(self, value: Dict[str, str]):
        """One or more key-value pairs for the client app to use in the challenge to be presented to the user.
        This parameter should contain all of the necessary information to accurately present the challenge to
        the user."""
        self["response"]["publicChallengeParameters"] = value

    @property
    def private_challenge_parameters(self) -> Dict[str, str]:
        return self["response"]["privateChallengeParameters"]

    @private_challenge_parameters.setter
    def private_challenge_parameters(self, value: Dict[str, str]):
        """This parameter is only used by the Verify Auth Challenge Response Lambda trigger.
        This parameter should contain all of the information that is required to validate the user's
        response to the challenge. In other words, the publicChallengeParameters parameter contains the
        question that is presented to the user and privateChallengeParameters contains the valid answers
        for the question."""
        self["response"]["privateChallengeParameters"] = value

    @property
    def challenge_metadata(self) -> str:
        return self["response"]["challengeMetadata"]

    @challenge_metadata.setter
    def challenge_metadata(self, value: str):
        """Your name for the custom challenge, if this is a custom challenge."""
        self["response"]["challengeMetadata"] = value


class CreateAuthChallengeTriggerEvent(BaseTriggerEvent):
    """Create Auth Challenge Lambda Trigger

    Amazon Cognito invokes this trigger after Define Auth Challenge if a custom challenge has been
    specified as part of the Define Auth Challenge trigger.
    It creates a custom authentication flow.

    Notes:
    ----
    `triggerSource` can be one of the following:

    - `CreateAuthChallenge_Authentication` Create Auth Challenge.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-create-auth-challenge.html
    """

    @property
    def request(self) -> CreateAuthChallengeTriggerEventRequest:
        """Create Auth Challenge Request Parameters"""
        return CreateAuthChallengeTriggerEventRequest(self._data)

    @property
    def response(self) -> CreateAuthChallengeTriggerEventResponse:
        """Create Auth Challenge Response Parameters"""
        return CreateAuthChallengeTriggerEventResponse(self._data)


class VerifyAuthChallengeResponseTriggerEventRequest(DictWrapper):
    @property
    def user_attributes(self) -> Dict[str, str]:
        """One or more name-value pairs representing user attributes. The attribute names are the keys."""
        return self["request"]["userAttributes"]

    @property
    def private_challenge_parameters(self) -> Dict[str, str]:
        """This parameter comes from the Create Auth Challenge trigger, and is
        compared against a user’s challengeAnswer to determine whether the user passed the challenge."""
        return self["request"]["privateChallengeParameters"]

    @property
    def challenge_answer(self) -> Any:
        """The answer from the user's response to the challenge."""
        return self["request"]["challengeAnswer"]

    @property
    def client_metadata(self) -> Optional[Dict[str, str]]:
        """One or more key-value pairs that you can provide as custom input to the Lambda function that
        you specify for the verify auth challenge trigger."""
        return self["request"].get("clientMetadata")

    @property
    def user_not_found(self) -> Optional[bool]:
        """This boolean is populated when PreventUserExistenceErrors is set to ENABLED for your User Pool client."""
        return self["request"].get("userNotFound")


class VerifyAuthChallengeResponseTriggerEventResponse(DictWrapper):
    @property
    def answer_correct(self) -> bool:
        return bool(self["response"]["answerCorrect"])

    @answer_correct.setter
    def answer_correct(self, value: bool):
        """Set to true if the user has successfully completed the challenge, or false otherwise."""
        self["response"]["answerCorrect"] = value


class VerifyAuthChallengeResponseTriggerEvent(BaseTriggerEvent):
    """Verify Auth Challenge Response Lambda Trigger

    Amazon Cognito invokes this trigger to verify if the response from the end user for a custom
    Auth Challenge is valid or not.
    It is part of a user pool custom authentication flow.

    Notes:
    ----
    `triggerSource` can be one of the following:

    - `VerifyAuthChallengeResponse_Authentication` Verify Auth Challenge Response.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-verify-auth-challenge-response.html
    """

    @property
    def request(self) -> VerifyAuthChallengeResponseTriggerEventRequest:
        """Verify Auth Challenge Request Parameters"""
        return VerifyAuthChallengeResponseTriggerEventRequest(self._data)

    @property
    def response(self) -> VerifyAuthChallengeResponseTriggerEventResponse:
        """Verify Auth Challenge Response Parameters"""
        return VerifyAuthChallengeResponseTriggerEventResponse(self._data)
