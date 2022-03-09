from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import CreateAuthChallengeTriggerEvent


@event_source(data_class=CreateAuthChallengeTriggerEvent)
def handler(event: CreateAuthChallengeTriggerEvent, context) -> dict:
    if event.request.challenge_name == "CUSTOM_CHALLENGE":
        event.response.public_challenge_parameters = {"captchaUrl": "url/123.jpg"}
        event.response.private_challenge_parameters = {"answer": "5"}
        event.response.challenge_metadata = "CAPTCHA_CHALLENGE"
    return event.raw_event
