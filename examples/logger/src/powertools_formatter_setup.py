from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter

# NOTE: Check docs for all available options
# https://awslabs.github.io/aws-lambda-powertools-python/latest/core/logger/#lambdapowertoolsformatter

formatter = LambdaPowertoolsFormatter(utc=True, log_record_order=["message"])
logger = Logger(service="example", logger_formatter=formatter)
