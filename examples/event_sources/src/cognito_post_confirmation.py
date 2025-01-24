from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import PostConfirmationTriggerEvent


def lambda_handler(event, context):
    event: PostConfirmationTriggerEvent = PostConfirmationTriggerEvent(event)

    user_attributes = event.request.user_attributes

    return {"statusCode": 200, "body": f"User attributes: {user_attributes}"}
