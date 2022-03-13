from aws_lambda_powertools import Logger

logger = Logger(service="payment")


@logger.inject_lambda_context
def handler(event, context):
    logger.info("Collecting payment")

    # You can log entire objects too
    logger.info(
        {
            "operation": "collect_payment",
            "charge_id": event["charge_id"],
        }
    )
    ...
