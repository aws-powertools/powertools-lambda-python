from aws_lambda_powertools import Logger

logger = Logger(service="payment")


def handler(event, context):
    logger.append_keys(sample_key="value")
    logger.info("Collecting payment")

    logger.remove_keys(["sample_key"])
    logger.info("Collecting payment without sample key")
