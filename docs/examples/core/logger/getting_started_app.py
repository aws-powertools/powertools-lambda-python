from aws_lambda_powertools import Logger

logger = Logger()  # Sets service via env var
# OR logger = Logger(service="example")
