from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter

formatter = LambdaPowertoolsFormatter(
    utc=True,
    log_record_order=["message"],
)
logger = Logger(service="example", logger_formatter=formatter)
