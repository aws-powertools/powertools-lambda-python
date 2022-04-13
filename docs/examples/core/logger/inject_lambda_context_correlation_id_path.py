from aws_lambda_powertools import Logger

logger = Logger(service="payment")


@logger.inject_lambda_context(correlation_id_path="headers.my_request_id_header")
def handler(event, context):
    logger.debug(f"Correlation ID => {logger.get_correlation_id()}")
    logger.info("Collecting payment")
