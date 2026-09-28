from typing import Any, Dict, List, Literal

from pydantic import BaseModel


# Common context model for Cognito triggers
class CognitoCallerContextModel(BaseModel):
    awsSdkVersion: str
    clientId: str


# Base model for all Cognito triggers
class CognitoTriggerBaseSchema(BaseModel):
    version: str
    region: str
    userPoolId: str
    userName: str | None = None
    callerContext: CognitoCallerContextModel


# Models for Pre-Signup flow
class CognitoPreSignupRequestModel(BaseModel):
    userAttributes: Dict[str, Any]
    validationData: Dict[str, Any] | None = None
    clientMetadata: Dict[str, Any] | None = None
    userNotFound: bool | None = None


class CognitoPreSignupResponseModel(BaseModel):
    autoConfirmUser: bool | None = False
    autoVerifyPhone: bool | None = False
    autoVerifyEmail: bool | None = False


class CognitoPreSignupTriggerModel(CognitoTriggerBaseSchema):
    triggerSource: Literal["PreSignUp_SignUp"]
    request: CognitoPreSignupRequestModel
    response: CognitoPreSignupResponseModel


# Models for Post-Confirmation flow
class CognitoPostConfirmationRequestModel(BaseModel):
    userAttributes: Dict[str, Any]
    clientMetadata: Dict[str, Any] | None = None


class CognitoPostConfirmationTriggerModel(CognitoTriggerBaseSchema):
    triggerSource: Literal["PostConfirmation_ConfirmSignUp"]
    request: CognitoPostConfirmationRequestModel
    response: Dict[str, Any] = {}


# Models for Pre-Authentication flow
class CognitoPreAuthenticationRequestModel(BaseModel):
    userAttributes: Dict[str, Any]
    validationData: Dict[str, Any] | None = None
    userNotFound: bool | None = None


class CognitoPreAuthenticationTriggerModel(CognitoTriggerBaseSchema):
    triggerSource: Literal["PreAuthentication_Authentication"]
    request: CognitoPreAuthenticationRequestModel
    response: Dict[str, Any] = {}


# Models for Post-Authentication flow
class CognitoPostAuthenticationRequestModel(BaseModel):
    userAttributes: Dict[str, Any]
    newDeviceUsed: bool | None = None
    clientMetadata: Dict[str, Any] | None = None


class CognitoPostAuthenticationTriggerModel(CognitoTriggerBaseSchema):
    triggerSource: Literal["PostAuthentication_Authentication"]
    request: CognitoPostAuthenticationRequestModel
    response: Dict[str, Any] = {}


# Models for Pre-Token Generation flow
class CognitoGroupConfigurationModel(BaseModel):
    groupsToOverride: List[str]
    iamRolesToOverride: List[str]
    preferredRole: str | None = None


class CognitoPreTokenGenerationRequestModel(BaseModel):
    userAttributes: Dict[str, Any]
    groupConfiguration: CognitoGroupConfigurationModel
    clientMetadata: Dict[str, Any] | None = None


class CognitoPreTokenGenerationTriggerModelV1(CognitoTriggerBaseSchema):
    triggerSource: str
    request: CognitoPreTokenGenerationRequestModel
    response: Dict[str, Any] = {}


class CognitoPreTokenGenerationRequestModelV2AndV3(CognitoPreTokenGenerationRequestModel):
    scopes: Dict[str, Any] | None = None


class CognitoPreTokenGenerationTriggerModelV2AndV3(CognitoTriggerBaseSchema):
    request: CognitoPreTokenGenerationRequestModelV2AndV3
    response: Dict[str, Any] = {}


# Models for User Migration flow
class CognitoMigrateUserRequestModel(BaseModel):
    password: str
    validationData: Dict[str, Any] | None = None
    clientMetadata: Dict[str, Any] | None = None


class CognitoMigrateUserResponseModel(BaseModel):
    userAttributes: Dict[str, Any] | None = None
    finalUserStatus: str | None = None
    messageAction: str | None = None
    desiredDeliveryMediums: List[str] | None = None
    forceAliasCreation: bool | None = None
    enableSMSMFA: bool | None = None


class CognitoMigrateUserTriggerModel(CognitoTriggerBaseSchema):
    triggerSource: str
    userName: str
    request: CognitoMigrateUserRequestModel
    response: CognitoMigrateUserResponseModel


# Models for Custom Message flow
class CognitoCustomMessageRequestModel(BaseModel):
    userAttributes: Dict[str, Any]
    codeParameter: str
    linkParameter: str | None = None
    usernameParameter: str | None = None
    clientMetadata: Dict[str, Any] | None = None


class CognitoCustomMessageResponseModel(BaseModel):
    smsMessage: str | None = None
    emailMessage: str | None = None
    emailSubject: str | None = None


class CognitoCustomMessageTriggerModel(CognitoTriggerBaseSchema):
    triggerSource: str
    request: CognitoCustomMessageRequestModel
    response: CognitoCustomMessageResponseModel


# Models for Custom Email/SMS Sender flow
class CognitoCustomEmailSMSSenderRequestModel(BaseModel):
    type: str
    code: str
    clientMetadata: Dict[str, Any] | None = None
    userAttributes: Dict[str, Any]


class CognitoCustomEmailSenderTriggerModel(CognitoTriggerBaseSchema):
    triggerSource: Literal["CustomEmailSender_SignUp"]
    request: CognitoCustomEmailSMSSenderRequestModel


class CognitoCustomSMSSenderTriggerModel(CognitoTriggerBaseSchema):
    triggerSource: Literal["CustomSMSSender_SignUp"]
    request: CognitoCustomEmailSMSSenderRequestModel


# Models for Challenge Authentication flows
class CognitoChallengeResultModel(BaseModel):
    challengeName: Literal[
        "SRP_A",
        "PASSWORD_VERIFIER",
        "SMS_MFA",
        "EMAIL_OTP",
        "SOFTWARE_TOKEN_MFA",
        "DEVICE_SRP_AUTH",
        "DEVICE_PASSWORD_VERIFIER",
        "ADMIN_NO_SRP_AUTH",
    ]
    challengeResult: bool
    challengeMetadata: str | None = None


class CognitoAuthChallengeRequestModel(BaseModel):
    userAttributes: Dict[str, Any]
    session: List[CognitoChallengeResultModel]
    clientMetadata: Dict[str, Any] | None = None
    userNotFound: bool | None = None


class CognitoDefineAuthChallengeResponseModel(BaseModel):
    challengeName: str | None = None
    issueTokens: bool | None = None
    failAuthentication: bool | None = None


class CognitoDefineAuthChallengeTriggerModel(CognitoTriggerBaseSchema):
    triggerSource: Literal["DefineAuthChallenge_Authentication"]
    request: CognitoAuthChallengeRequestModel
    response: CognitoDefineAuthChallengeResponseModel


class CognitoCreateAuthChallengeResponseModel(BaseModel):
    publicChallengeParameters: Dict[str, Any] | None = None
    privateChallengeParameters: Dict[str, Any] | None = None
    challengeMetadata: str | None = None


class CognitoCreateAuthChallengeTriggerModel(CognitoTriggerBaseSchema):
    triggerSource: Literal["CreateAuthChallenge_Authentication"]
    request: CognitoAuthChallengeRequestModel
    response: CognitoCreateAuthChallengeResponseModel


class CognitoVerifyAuthChallengeRequestModel(BaseModel):
    userAttributes: Dict[str, Any]
    privateChallengeParameters: Dict[str, Any]
    challengeAnswer: str
    clientMetadata: Dict[str, Any] | None = None
    userNotFound: bool | None = None


class CognitoVerifyAuthChallengeResponseModel(BaseModel):
    answerCorrect: bool


class CognitoVerifyAuthChallengeTriggerModel(CognitoTriggerBaseSchema):
    triggerSource: Literal["VerifyAuthChallengeResponse_Authentication"]
    request: CognitoVerifyAuthChallengeRequestModel
    response: CognitoVerifyAuthChallengeResponseModel
