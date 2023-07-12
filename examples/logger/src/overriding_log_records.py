from aws_lambda_powertools import Logger

location_format = "[%(funcName)s] %(module)s"

# override location and timestamp format
logger = Logger(service="payment", location=location_format)
logger.info("Collecting payment")

# suppress keys with a None value
logger_two = Logger(service="loyalty", location=None)
logger_two.info("Calculating points")
