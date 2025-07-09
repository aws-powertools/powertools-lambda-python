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
    CognitoPreTokenGenerationTriggerModel,
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
        ("cognitoPreTokenGenerationEvent.json", CognitoPreTokenGenerationTriggerModel),
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
