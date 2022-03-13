from aws_lambda_powertools import Logger

logger = Logger(service="payment")


@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    ...
