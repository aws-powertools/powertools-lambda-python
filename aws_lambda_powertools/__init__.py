# -*- coding: utf-8 -*-

"""Top-level package for Lambda Python Powertools."""

from pathlib import Path

from .logging import Logger
from .metrics import Metrics, single_metric
from .package_logger import set_package_logger_handler
from .shared import add_user_agent
from .tracing import Tracer

__author__ = """Amazon Web Services"""
__all__ = [
    "Logger",
    "Metrics",
    "single_metric",
    "Tracer",
]

PACKAGE_PATH = Path(__file__).parent

set_package_logger_handler()

add_user_agent.register_user_agent()
