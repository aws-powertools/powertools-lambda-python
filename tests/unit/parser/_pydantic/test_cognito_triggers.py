import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, parse
from aws_lambda_powertools.utilities.parser.models import (
    CognitoCreateAuthChallengeTriggerModel,
    CognitoCustomEmailSenderTriggerModel,
    CognitoCustomMessageTriggerModel,
    CognitoCustomSMSSenderTriggerModel,
    CognitoDefineAuthChallengeTriggerModel,
    CognitoMigrateUserTriggerModel,
    CognitoPostAuthenticationTriggerModel,
    CognitoPostConfirmationTriggerModel,
    CognitoPreAuthenticationTriggerModel,
    CognitoPreSignupTriggerModel,
    CognitoPreTokenGenerationTriggerModelV1,
    CognitoVerifyAuthChallengeTriggerModel,
)
from tests.functional.utils import load_event


@pytest.mark.parametrize(
    "filename,model",
    [
        # use the existing `tests/events/*.json` names:
        ("cognitoPreSignUpEvent.json", CognitoPreSignupTriggerModel),
        ("cognitoPostConfirmationEvent.json", CognitoPostConfirmationTriggerModel),
        ("cognitoPreAuthenticationEvent.json", CognitoPreAuthenticationTriggerModel),
        ("cognitoPostAuthenticationEvent.json", CognitoPostAuthenticationTriggerModel),
        ("cognitoPreTokenGenerationEvent.json", CognitoPreTokenGenerationTriggerModelV1),
        ("cognitoUserMigrationEvent.json", CognitoMigrateUserTriggerModel),
        ("cognitoCustomMessageEvent.json", CognitoCustomMessageTriggerModel),
        ("cognitoCustomEmailSenderEvent.json", CognitoCustomEmailSenderTriggerModel),
        ("cognitoCustomSMSSenderEvent.json", CognitoCustomSMSSenderTriggerModel),
        ("cognitoDefineAuthChallengeEvent.json", CognitoDefineAuthChallengeTriggerModel),
        ("cognitoCreateAuthChallengeEvent.json", CognitoCreateAuthChallengeTriggerModel),
        ("cognitoVerifyAuthChallengeResponseEvent.json", CognitoVerifyAuthChallengeTriggerModel),
    ],
)
def test_cognito_trigger_models_parse_success(filename, model):
    event = load_event(filename)
    parsed = parse(event=event, model=model)
    # if parsing succeeds, we get an instance
    assert isinstance(parsed, model)


def test_cognito_trigger_models_invalid_raises():
    with pytest.raises(ValidationError):
        parse(event={"foo": "bar"}, model=CognitoPreSignupTriggerModel)


@pytest.mark.parametrize(
    "filename,model,trigger_source",
    [
        ("cognitoPreSignUpEvent.json", CognitoPreSignupTriggerModel, "PreSignUp_AdminCreateUser"),
        ("cognitoPreSignUpEvent.json", CognitoPreSignupTriggerModel, "PreSignUp_ExternalProvider"),
        (
            "cognitoPostConfirmationEvent.json",
            CognitoPostConfirmationTriggerModel,
            "PostConfirmation_ConfirmForgotPassword",
        ),
        ("cognitoCustomEmailSenderEvent.json", CognitoCustomEmailSenderTriggerModel, "CustomEmailSender_ResendCode"),
        (
            "cognitoCustomEmailSenderEvent.json",
            CognitoCustomEmailSenderTriggerModel,
            "CustomEmailSender_ForgotPassword",
        ),
        (
            "cognitoCustomEmailSenderEvent.json",
            CognitoCustomEmailSenderTriggerModel,
            "CustomEmailSender_UpdateUserAttribute",
        ),
        (
            "cognitoCustomEmailSenderEvent.json",
            CognitoCustomEmailSenderTriggerModel,
            "CustomEmailSender_VerifyUserAttribute",
        ),
        (
            "cognitoCustomEmailSenderEvent.json",
            CognitoCustomEmailSenderTriggerModel,
            "CustomEmailSender_AdminCreateUser",
        ),
        (
            "cognitoCustomEmailSenderEvent.json",
            CognitoCustomEmailSenderTriggerModel,
            "CustomEmailSender_Authentication",
        ),
        (
            "cognitoCustomEmailSenderEvent.json",
            CognitoCustomEmailSenderTriggerModel,
            "CustomEmailSender_AccountTakeOverNotification",
        ),
        ("cognitoCustomSMSSenderEvent.json", CognitoCustomSMSSenderTriggerModel, "CustomSMSSender_ResendCode"),
        ("cognitoCustomSMSSenderEvent.json", CognitoCustomSMSSenderTriggerModel, "CustomSMSSender_ForgotPassword"),
        (
            "cognitoCustomSMSSenderEvent.json",
            CognitoCustomSMSSenderTriggerModel,
            "CustomSMSSender_UpdateUserAttribute",
        ),
        (
            "cognitoCustomSMSSenderEvent.json",
            CognitoCustomSMSSenderTriggerModel,
            "CustomSMSSender_VerifyUserAttribute",
        ),
        ("cognitoCustomSMSSenderEvent.json", CognitoCustomSMSSenderTriggerModel, "CustomSMSSender_AdminCreateUser"),
        ("cognitoCustomSMSSenderEvent.json", CognitoCustomSMSSenderTriggerModel, "CustomSMSSender_Authentication"),
    ],
)
def test_cognito_trigger_models_accept_documented_trigger_sources(filename, model, trigger_source):
    event = load_event(filename)
    event["triggerSource"] = trigger_source

    parsed = parse(event=event, model=model)

    assert parsed.triggerSource == trigger_source


@pytest.mark.parametrize(
    "filename,model",
    [
        ("cognitoDefineAuthChallengeEvent.json", CognitoDefineAuthChallengeTriggerModel),
        ("cognitoCreateAuthChallengeEvent.json", CognitoCreateAuthChallengeTriggerModel),
    ],
)
def test_cognito_auth_challenge_models_accept_custom_challenge_in_session(filename, model):
    event = load_event(filename)
    event["request"]["session"].append(
        {"challengeName": "CUSTOM_CHALLENGE", "challengeResult": True, "challengeMetadata": "CAPTCHA_CHALLENGE"},
    )

    parsed = parse(event=event, model=model)

    assert parsed.request.session[-1].challengeName == "CUSTOM_CHALLENGE"


def test_cognito_verify_auth_challenge_model_accepts_null_answer_correct():
    # Cognito sends answerCorrect as null, and the function sets it
    event = load_event("cognitoVerifyAuthChallengeResponseEvent.json")
    event["response"]["answerCorrect"] = None

    parsed = parse(event=event, model=CognitoVerifyAuthChallengeTriggerModel)

    assert parsed.response.answerCorrect is None


def test_cognito_trigger_models_accept_null_client_id():
    # Admin API operations such as AdminConfirmSignUp send clientId as null
    event = load_event("cognitoPostConfirmationEvent.json")
    event["callerContext"]["clientId"] = None

    parsed = parse(event=event, model=CognitoPostConfirmationTriggerModel)

    assert parsed.callerContext.clientId is None
