# -*- coding: utf-8 -*-

"""Top-level package for Lambda Python Powertools."""


from .logging import Logger  # noqa: F401
from .metrics import Metrics, single_metric  # noqa: F401
from .tracing import Tracer  # noqa: F401

__author__ = """Amazon Web Services"""


def set_package_logging_null_handler():
    import logging

    logger = logging.getLogger("aws_lambda_powertools")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False


set_package_logging_null_handler()
