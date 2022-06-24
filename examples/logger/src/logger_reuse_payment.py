from aws_lambda_powertools import Logger

logger = Logger()


def inject_payment_id(context):
    logger.append_keys(payment_id=context.get("payment_id"))
