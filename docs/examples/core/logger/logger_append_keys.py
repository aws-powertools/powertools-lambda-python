from aws_lambda_powertools import Logger

logger = Logger(service="payment")


def handler(event, context):
    order_id = event.get("order_id")

    # this will ensure order_id key always has the latest value before logging
    logger.append_keys(order_id=order_id)

    logger.info("Collecting payment")
