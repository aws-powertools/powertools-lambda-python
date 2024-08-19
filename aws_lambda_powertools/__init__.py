"""Top-level package for Lambda Python Powertools."""

from pathlib import Path

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.metrics import Metrics, single_metric
from aws_lambda_powertools.package_logger import set_package_logger_handler
from aws_lambda_powertools.shared.user_agent import inject_user_agent
from aws_lambda_powertools.shared.version import VERSION
from aws_lambda_powertools.tracing import Tracer

__version__ = VERSION
__author__ = """Amazon Web Services"""
__all__ = [
    "Logger",
    "Metrics",
    "single_metric",
    "Tracer",
]

PACKAGE_PATH = Path(__file__).parent

set_package_logger_handler()

inject_user_agent()
