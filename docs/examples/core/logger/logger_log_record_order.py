from aws_lambda_powertools import Logger

# make message as the first key
logger = Logger(service="payment", log_record_order=["message"])

# make request_id that will be added later as the first key
# Logger(service="payment", log_record_order=["request_id"])

# Default key sorting order when omit
# Logger(service="payment", log_record_order=["level","location","message","timestamp"])
