from typing import Dict, Optional


class CallerContext(dict):
    @property
    def aws_sdk_version(self) -> str:
        """The AWS SDK version number."""
        return self["awsSdkVersion"]

    @property
    def client_id(self) -> str:
        """The ID of the client associated with the user pool."""
        return self["clientId"]


class BaseTriggerEvent(dict):
    """Common attributes shared by all User Pool Lambda Trigger Events

    Documentation:
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
        return CallerContext(self["callerContext"])


class PreSignUpTriggerEventRequest(dict):
    @property
    def user_attributes(self) -> Dict[str, str]:
        """One or more name-value pairs representing user attributes. The attribute names are the keys."""
        return self["userAttributes"]

    @property
    def validation_data(self) -> Optional[Dict[str, str]]:
        """One or more name-value pairs containing the validation data in the request to register a user."""
        return self.get("validationData")

    @property
    def client_metadata(self) -> Optional[Dict[str, str]]:
        """One or more key-value pairs that you can provide as custom input to the Lambda function
        that you specify for the pre sign-up trigger."""
        return self.get("clientMetadata")


class PreSignUpTriggerEventResponse(dict):
    @property
    def auto_confirm_user(self) -> bool:
        """Set to true to auto-confirm the user, or false otherwise."""
        return bool(self["response"]["autoConfirmUser"])

    @auto_confirm_user.setter
    def auto_confirm_user(self, value: bool):
        self["response"]["autoConfirmUser"] = value

    @property
    def auto_verify_email(self) -> bool:
        """Set to true to set as verified the email of a user who is signing up, or false otherwise."""
        return bool(self["response"]["autoVerifyEmail"])

    @auto_verify_email.setter
    def auto_verify_email(self, value: bool):
        self["response"]["autoVerifyEmail"] = value

    @property
    def auto_verify_phone(self) -> bool:
        """Set to true to set as verified the phone number of a user who is signing up, or false otherwise."""
        return bool(self["response"]["autoVerifyPhone"])

    @auto_verify_phone.setter
    def auto_verify_phone(self, value: bool):
        self["response"]["autoVerifyPhone"] = value


class PreSignUpTriggerEvent(BaseTriggerEvent):
    """Pre Sign-up Lambda Trigger

    Documentation:
        https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-sign-up.html
    """

    @property
    def request(self) -> PreSignUpTriggerEventRequest:
        return PreSignUpTriggerEventRequest(self["request"])

    @property
    def response(self) -> PreSignUpTriggerEventResponse:
        return PreSignUpTriggerEventResponse(self)


class PostConfirmationTriggerEventRequest(dict):
    @property
    def user_attributes(self) -> Dict[str, str]:
        """One or more name-value pairs representing user attributes. The attribute names are the keys."""
        return self["userAttributes"]

    @property
    def client_metadata(self) -> Optional[Dict[str, str]]:
        """One or more key-value pairs that you can provide as custom input to the Lambda function that you
        specify for the post confirmation trigger."""
        return self.get("clientMetadata")


class PostConfirmationTriggerEvent(BaseTriggerEvent):
    """Post Confirmation Lambda Trigger

    Documentation:
        https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-post-confirmation.html
    """

    @property
    def request(self) -> PostConfirmationTriggerEventRequest:
        return PostConfirmationTriggerEventRequest(self["request"])
