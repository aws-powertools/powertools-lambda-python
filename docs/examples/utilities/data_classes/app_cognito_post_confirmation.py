from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import PostConfirmationTriggerEvent


def lambda_handler(event, context):
    event: PostConfirmationTriggerEvent = PostConfirmationTriggerEvent(event)

    user_attributes = event.request.user_attributes
    do_something_with(user_attributes)
