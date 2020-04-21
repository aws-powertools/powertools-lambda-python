# -*- coding: utf-8 -*-

"""Top-level package for Lambda Python Powertools."""
import logging
import os

__author__ = """Amazon Web Services"""


logger = logging.getLogger("aws_lambda_powertools")
log_level = os.getenv("POWERTOOLS_LOG_LEVEL")
logger.addHandler(logging.NullHandler())

if log_level:
    logger.setLevel(log_level)
