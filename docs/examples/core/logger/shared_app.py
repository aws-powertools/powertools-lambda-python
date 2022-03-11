import shared  # Creates a child logger named "payment.shared"

from aws_lambda_powertools import Logger

logger = Logger()  # POWERTOOLS_SERVICE_NAME: "payment"


def handler(event, context):
    shared.inject_payment_id(event)
    ...
