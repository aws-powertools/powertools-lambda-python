import logging

from aws_lambda_powertools.logging.logger import set_package_logger
from aws_lambda_powertools.shared.functions import powertools_debug_is_set


def set_package_logger_handler(stream=None):
    """Sets up Powertools for AWS Lambda (Python) package logging.

    By default, we discard any output to not interfere with customers logging.

    When POWERTOOLS_DEBUG env var is set, we setup `aws_lambda_powertools` logger in DEBUG level.

    Parameters
    ----------
    stream: sys.stdout
        log stream, stdout by default
    """

    if powertools_debug_is_set():
        return set_package_logger(stream=stream)

    logger = logging.getLogger("aws_lambda_powertools")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
