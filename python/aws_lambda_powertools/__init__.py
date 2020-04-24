# -*- coding: utf-8 -*-

"""Top-level package for Lambda Python Powertools."""
import logging

__author__ = """Amazon Web Services"""

logger = logging.getLogger("aws_lambda_powertools")
logger.addHandler(logging.NullHandler())
logger.propagate = False
