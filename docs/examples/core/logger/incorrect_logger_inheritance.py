import my_module

from aws_lambda_powertools import Logger

logger = Logger(service="payment")
...

# my_module.py
from aws_lambda_powertools import Logger

logger = Logger(child=True)
