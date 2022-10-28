from aws_lambda_powertools import Logger

date_format = "%m/%d/%Y %I:%M:%S %p"

logger = Logger(service="payment", use_rfc3339=True)
logger.info("Collecting payment")

logger_custom_format = Logger(service="loyalty", datefmt=date_format)
logger_custom_format.info("Calculating points")
