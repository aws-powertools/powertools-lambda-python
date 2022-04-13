from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import VerifyAuthChallengeResponseTriggerEvent


@event_source(data_class=VerifyAuthChallengeResponseTriggerEvent)
def handler(event: VerifyAuthChallengeResponseTriggerEvent, context) -> dict:
    event.response.answer_correct = (
        event.request.private_challenge_parameters.get("answer") == event.request.challenge_answer
    )
    return event.raw_event
