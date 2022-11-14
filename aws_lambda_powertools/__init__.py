# -*- coding: utf-8 -*-

"""Top-level package for Lambda Python Powertools."""

from pathlib import Path

from .logging import Logger
from .metrics import Metrics, single_metric
from .package_logger import set_package_logger_handler
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
