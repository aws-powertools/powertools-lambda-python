import logging


def set_package_logger_handler():
    logger = logging.getLogger("aws_lambda_powertools")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
