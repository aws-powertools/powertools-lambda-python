from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import DefineAuthChallengeTriggerEvent


def handler(event: dict, context) -> dict:
    event: DefineAuthChallengeTriggerEvent = DefineAuthChallengeTriggerEvent(event)
    if len(event.request.session) == 1 and event.request.session[0].challenge_name == "SRP_A":
        event.response.issue_tokens = False
        event.response.fail_authentication = False
        event.response.challenge_name = "PASSWORD_VERIFIER"
    elif (
        len(event.request.session) == 2
        and event.request.session[1].challenge_name == "PASSWORD_VERIFIER"
        and event.request.session[1].challenge_result
    ):
        event.response.issue_tokens = False
        event.response.fail_authentication = False
        event.response.challenge_name = "CUSTOM_CHALLENGE"
    elif (
        len(event.request.session) == 3
        and event.request.session[2].challenge_name == "CUSTOM_CHALLENGE"
        and event.request.session[2].challenge_result
    ):
        event.response.issue_tokens = True
        event.response.fail_authentication = False
    else:
        event.response.issue_tokens = False
        event.response.fail_authentication = True

    return event.raw_event
