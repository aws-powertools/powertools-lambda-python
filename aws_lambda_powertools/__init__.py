# -*- coding: utf-8 -*-

"""Top-level package for Lambda Python Powertools."""


from .logging import Logger  # noqa: F401
from .metrics import Metrics, single_metric  # noqa: F401
from .package_logger import set_package_logger_handler
from .tracing import Tracer  # noqa: F401

__author__ = """Amazon Web Services"""

set_package_logger_handler()
