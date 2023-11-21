from aws_lambda_powertools import Logger

logger = Logger(level="ERROR")

print(logger.log_level)  # returns 40 (ERROR)
