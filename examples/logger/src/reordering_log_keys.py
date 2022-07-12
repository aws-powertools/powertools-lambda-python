from aws_lambda_powertools import Logger

# make message as the first key
logger = Logger(service="payment", log_record_order=["message"])

# make request_id that will be added later as the first key
logger_two = Logger(service="order", log_record_order=["request_id"])
logger_two.append_keys(request_id="123")

logger.info("hello world")
logger_two.info("hello world")
