from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CognitoCallerContextModel(BaseModel):
    awsSdkVersion: str
    clientId: str


class CognitoChallengeResultModel(BaseModel):
    challengeName: str
    challengeResult: bool
    challengeMetadata: Optional[str]


class CognitoPreSignupRequestModel(BaseModel):
    userAttributes: Dict[str, str]
    validationData: Optional[Dict[str, str]] = None
    clientMetadata: Optional[Dict[str, str]] = None


class CognitoPreSignupResponseModel(BaseModel):
    autoConfirmUser: Optional[bool] = None
    autoVerifyPhone: Optional[bool] = None
    autoVerifyEmail: Optional[bool] = None


class CognitoPreSignupTriggerModel(BaseModel):
    version: str
    region: str
    userPoolId: str
    userName: str
    callerContext: CognitoCallerContextModel
    triggerSource: str
    request: CognitoPreSignupRequestModel
    response: CognitoPreSignupResponseModel


class CognitoPostConfirmationRequestModel(BaseModel):
    userAttributes: Dict[str, str]
    clientMetadata: Optional[Dict[str, str]] = None


class CognitoPostConfirmationTriggerModel(BaseModel):
    version: str
    region: str
    userPoolId: str
    userName: str
    callerContext: CognitoCallerContextModel
    triggerSource: str
    request: CognitoPostConfirmationRequestModel
    response: Dict[str, Any] = {}


class CognitoPreAuthenticationRequestModel(BaseModel):
    userAttributes: Dict[str, str]
    validationData: Optional[Dict[str, str]] = None
    userNotFound: Optional[bool] = None


class CognitoPreAuthenticationTriggerModel(BaseModel):
    version: str
    region: str
    userPoolId: str
    userName: str
    callerContext: CognitoCallerContextModel
    triggerSource: str
    request: CognitoPreAuthenticationRequestModel
    response: Dict[str, Any] = {}


class CognitoPostAuthenticationRequestModel(BaseModel):
    userAttributes: Dict[str, str]
    newDeviceUsed: bool
    clientMetadata: Optional[Dict[str, str]] = None


class CognitoPostAuthenticationTriggerModel(BaseModel):
    version: str
    region: str
    userPoolId: str
    userName: str
    callerContext: CognitoCallerContextModel
    triggerSource: str
    request: CognitoPostAuthenticationRequestModel
    response: Dict[str, Any] = {}


class CognitoGroupConfigurationModel(BaseModel):
    groupsToOverride: List[str]
    iamRolesToOverride: List[str]
    preferredRole: Optional[str] = None


class CognitoPreTokenGenRequestModel(BaseModel):
    userAttributes: Dict[str, str]
    groupConfiguration: CognitoGroupConfigurationModel
    clientMetadata: Optional[Dict[str, str]] = None


class CognitoClaimsOverrideDetailsModel(BaseModel):
    claimsToAddOrOverride: Optional[Dict[str, str]] = None
    claimsToSuppress: Optional[List[str]] = None
    groupOverrideDetails: Optional[CognitoGroupConfigurationModel] = None


class CognitoPreTokenGenResponseModel(BaseModel):
    claimsOverrideDetails: Optional[CognitoClaimsOverrideDetailsModel] = None


class CognitoPreTokenGenerationTriggerModel(BaseModel):
    version: str
    region: str
    userPoolId: str
    userName: str
    callerContext: CognitoCallerContextModel
    triggerSource: str
    request: CognitoPreTokenGenRequestModel
    response: CognitoPreTokenGenResponseModel


class CognitoMigrateUserRequestModel(BaseModel):
    password: str
    validationData: Optional[Dict[str, str]] = None
    clientMetadata: Optional[Dict[str, str]] = None


class CognitoMigrateUserResponseModel(BaseModel):
    userAttributes: Dict[str, str]
    finalUserStatus: Optional[str] = None
    messageAction: Optional[str] = None
    desiredDeliveryMediums: Optional[List[str]] = None
    forceAliasCreation: Optional[bool] = None
    enableSMSMFA: Optional[bool] = None


class CognitoMigrateUserTriggerModel(BaseModel):
    userName: str
    version: Optional[str] = None
    region: Optional[str] = None
    userPoolId: Optional[str] = None
    callerContext: Optional[CognitoCallerContextModel] = None
    triggerSource: Optional[str] = None
    request: CognitoMigrateUserRequestModel
    response: CognitoMigrateUserResponseModel


class CognitoCustomMessageRequestModel(BaseModel):
    userAttributes: Dict[str, str]
    codeParameter: Optional[str] = None
    usernameParameter: Optional[str] = None
    clientMetadata: Optional[Dict[str, str]] = None


class CognitoCustomMessageResponseModel(BaseModel):
    smsMessage: Optional[str] = None
    emailMessage: Optional[str] = None
    emailSubject: Optional[str] = None


class CognitoCustomMessageTriggerModel(BaseModel):
    version: str
    region: str
    userPoolId: str
    userName: str
    callerContext: CognitoCallerContextModel
    triggerSource: str
    request: CognitoCustomMessageRequestModel
    response: CognitoCustomMessageResponseModel


class CognitoCustomEmailSenderRequestModel(BaseModel):
    type: str
    code: str
    clientMetadata: Optional[Dict[str, str]] = None
    userAttributes: Dict[str, str]


class CognitoCustomEmailSenderTriggerModel(BaseModel):
    version: str
    region: str
    userPoolId: str
    userName: str
    callerContext: CognitoCallerContextModel
    triggerSource: str
    request: CognitoCustomEmailSenderRequestModel


class CognitoCustomSMSSenderRequestModel(BaseModel):
    type: str
    code: str
    clientMetadata: Optional[Dict[str, str]] = None
    userAttributes: Dict[str, str]


class CognitoCustomSMSSenderTriggerModel(BaseModel):
    version: str
    region: str
    userPoolId: str
    userName: str
    callerContext: CognitoCallerContextModel
    triggerSource: str
    request: CognitoCustomSMSSenderRequestModel


class CognitoDefineAuthChallengeRequestModel(BaseModel):
    userAttributes: Dict[str, str]
    session: List[CognitoChallengeResultModel]
    clientMetadata: Optional[Dict[str, str]] = None
    userNotFound: Optional[bool] = None


class CognitoDefineAuthChallengeResponseModel(BaseModel):
    challengeName: str
    issueTokens: bool
    failAuthentication: bool


class CognitoDefineAuthChallengeTriggerModel(BaseModel):
    version: str
    region: str
    userPoolId: str
    userName: str
    callerContext: CognitoCallerContextModel
    triggerSource: str
    request: CognitoDefineAuthChallengeRequestModel
    response: CognitoDefineAuthChallengeResponseModel


class CognitoCreateAuthChallengeRequestModel(BaseModel):
    userAttributes: Dict[str, str]
    challengeName: str
    session: List[CognitoChallengeResultModel]
    clientMetadata: Optional[Dict[str, str]] = None
    userNotFound: Optional[bool] = None


class CognitoCreateAuthChallengeResponseModel(BaseModel):
    publicChallengeParameters: Dict[str, str]
    privateChallengeParameters: Dict[str, str]
    challengeMetadata: Optional[str] = None


class CognitoCreateAuthChallengeTriggerModel(BaseModel):
    version: str
    region: str
    userPoolId: str
    userName: str
    callerContext: CognitoCallerContextModel
    triggerSource: str
    request: CognitoCreateAuthChallengeRequestModel
    response: CognitoCreateAuthChallengeResponseModel


class CognitoVerifyAuthChallengeRequestModel(BaseModel):
    userAttributes: Dict[str, str]
    privateChallengeParameters: Dict[str, str]
    challengeAnswer: str
    clientMetadata: Optional[Dict[str, str]] = None
    userNotFound: Optional[bool] = None


class CognitoVerifyAuthChallengeResponseModel(BaseModel):
    answerCorrect: bool


class CognitoVerifyAuthChallengeTriggerModel(BaseModel):
    version: str
    region: str
    userPoolId: str
    userName: str
    callerContext: CognitoCallerContextModel
    triggerSource: str
    request: CognitoVerifyAuthChallengeRequestModel
    response: CognitoVerifyAuthChallengeResponseModel
