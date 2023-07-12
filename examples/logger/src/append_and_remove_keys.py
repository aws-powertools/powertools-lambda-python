from aws_lambda_powertools import Logger

logger = Logger(service="payment", name="%(name)s")

logger.info("Name should be equal service value")

additional_log_attributes = {"process": "%(process)d", "processName": "%(processName)s"}
logger.append_keys(**additional_log_attributes)
logger.info("This will include process ID and name")
logger.remove_keys(["processName"])

# further messages will not include processName
