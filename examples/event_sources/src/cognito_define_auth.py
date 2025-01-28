from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import DefineAuthChallengeTriggerEvent


def lambda_handler(event, context) -> dict:
    event_obj: DefineAuthChallengeTriggerEvent = DefineAuthChallengeTriggerEvent(event)

    if len(event_obj.request.session) == 1 and event_obj.request.session[0].challenge_name == "SRP_A":
        event_obj.response.issue_tokens = False
        event_obj.response.fail_authentication = False
        event_obj.response.challenge_name = "PASSWORD_VERIFIER"
    elif (
        len(event_obj.request.session) == 2
        and event_obj.request.session[1].challenge_name == "PASSWORD_VERIFIER"
        and event_obj.request.session[1].challenge_result
    ):
        event_obj.response.issue_tokens = False
        event_obj.response.fail_authentication = False
        event_obj.response.challenge_name = "CUSTOM_CHALLENGE"
    elif (
        len(event_obj.request.session) == 3
        and event_obj.request.session[2].challenge_name == "CUSTOM_CHALLENGE"
        and event_obj.request.session[2].challenge_result
    ):
        event_obj.response.issue_tokens = True
        event_obj.response.fail_authentication = False
    else:
        event_obj.response.issue_tokens = False
        event_obj.response.fail_authentication = True

    return event_obj.raw_event
