import importlib
import time
from contextlib import contextmanager
from types import ModuleType
from typing import Generator, Tuple

import pytest

LOGGER_INIT_SLA: float = 0.001
METRICS_INIT_SLA: float = 0.005
TRACER_INIT_SLA: float = 0.5
IMPORT_INIT_SLA: float = 0.035


@contextmanager
def timing() -> Generator:
    """ "Generator to quickly time operations. It can add 5ms so take that into account in elapsed time

    Examples
    --------

        with timing() as t:
            print("something")
        elapsed = t()
    """
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start  # gen as lambda to calculate elapsed time


def core_utilities() -> Tuple[ModuleType, ModuleType, ModuleType]:
    """Return Tracing, Logging, and Metrics module"""
    tracing = importlib.import_module("aws_lambda_powertools.tracing")
    logging = importlib.import_module("aws_lambda_powertools.logging")
    metrics = importlib.import_module("aws_lambda_powertools.metrics")

    return tracing, logging, metrics


@pytest.mark.perf
def test_import_times_ceiling():
    # GIVEN Core utilities are imported
    # WHEN none are used
    # THEN import and any global initialization perf should be below 30ms
    # though we adjust to 35ms to take into account different CI machines, etc.
    # instead of re-running tests which can lead to false positives
    with timing() as t:
        core_utilities()

    elapsed = t()
    if elapsed > IMPORT_INIT_SLA:
        pytest.fail(f"High level imports should be below 35ms: {elapsed}")


@pytest.mark.perf
def test_tracer_init():
    # GIVEN Tracer is initialized
    # WHEN default options are used
    # THEN initialization X-Ray SDK perf should be below 450ms
    # though we adjust to 500ms to take into account different CI machines, etc.
    # instead of re-running tests which can lead to false positives
    with timing() as t:
        tracing, _, _ = core_utilities()
        tracing.Tracer(disabled=True)  # boto3 takes ~200ms, and remaining is X-Ray SDK init

    elapsed = t()
    if elapsed > TRACER_INIT_SLA:
        pytest.fail(f"High level imports should be below 50ms: {elapsed}")


@pytest.mark.perf
def test_metrics_init():
    # GIVEN Metrics is initialized
    # WHEN default options are used
    # THEN initialization perf should be below 5ms
    with timing() as t:
        _, _, metrics = core_utilities()
        metrics.Metrics()

    elapsed = t()
    if elapsed > METRICS_INIT_SLA:
        pytest.fail(f"High level imports should be below 40ms: {elapsed}")


@pytest.mark.perf
def test_logger_init():
    # GIVEN Logger is initialized
    # WHEN default options are used
    # THEN initialization perf should be below 5ms
    with timing() as t:
        _, logging, _ = core_utilities()
        logging.Logger()

    elapsed = t()
    if elapsed > LOGGER_INIT_SLA:
        pytest.fail(f"High level imports should be below 40ms: {elapsed}")
