from aws_lambda_powertools import Logger

date_format = "%m/%d/%Y %I:%M:%S %p"
location_format = "[%(funcName)s] %(module)s -pants"

# override location and timestamp format
logger = Logger(
    service="payment",
    location=location_format,
    datefmt=date_format,
)

# suppress the location key with a None value
logger_two = Logger(service="payment", location=None)

logger.info("Collecting payment")
