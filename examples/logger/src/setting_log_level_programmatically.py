from aws_lambda_powertools import Logger

logger = Logger()

# print default log level
print(logger.log_level)  # returns 20 (INFO)

# Setting programmatic log level
logger.setLevel("DEBUG")

# print new log level
print(logger.log_level)  # returns 10 (DEBUG)
