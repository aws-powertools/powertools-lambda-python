import importlib
from types import ModuleType
from typing import Tuple

import pytest

LOGGER_INIT_SLA: float = 0.005
METRICS_INIT_SLA: float = 0.005
TRACER_INIT_SLA: float = 0.5
IMPORT_INIT_SLA: float = 0.035
PARENT_PACKAGE = "aws_lambda_powertools"
TRACING_PACKAGE = "aws_lambda_powertools.tracing"
LOGGING_PACKAGE = "aws_lambda_powertools.logging"
METRICS_PACKAGE = "aws_lambda_powertools.metrics"


def import_core_utilities() -> Tuple[ModuleType, ModuleType, ModuleType]:
    """Dynamically imports and return Tracing, Logging, and Metrics modules"""
    return (
        importlib.import_module(TRACING_PACKAGE),
        importlib.import_module(LOGGING_PACKAGE),
        importlib.import_module(METRICS_PACKAGE),
    )


@pytest.fixture(autouse=True)
def clear_cache():
    importlib.invalidate_caches()


def import_init_tracer():
    tracing = importlib.import_module(TRACING_PACKAGE)
    tracing.Tracer(disabled=True)


def import_init_metrics():
    metrics = importlib.import_module(METRICS_PACKAGE)
    metrics.Metrics()


def import_init_logger():
    logging = importlib.import_module(LOGGING_PACKAGE)
    logging.Logger()


@pytest.mark.perf
@pytest.mark.benchmark(group="core", disable_gc=True, warmup=False)
def test_import_times_ceiling(benchmark):
    # GIVEN Core utilities are imported
    # WHEN none are used
    # THEN import and any global initialization perf should be below 30ms
    # though we adjust to 35ms to take into account different CI machines, etc.
    # instead of re-running tests which can lead to false positives
    benchmark.pedantic(import_core_utilities)
    stat = benchmark.stats.stats.max
    if stat > IMPORT_INIT_SLA:
        pytest.fail(f"High level imports should be below {IMPORT_INIT_SLA}s: {stat}")


@pytest.mark.perf
@pytest.mark.benchmark(group="core", disable_gc=True, warmup=False)
def test_tracer_init(benchmark):
    # GIVEN Tracer is initialized
    # WHEN default options are used
    # THEN initialization X-Ray SDK perf should be below 450ms
    # though we adjust to 500ms to take into account different CI machines, etc.
    # instead of re-running tests which can lead to false positives
    benchmark.pedantic(import_init_tracer)
    stat = benchmark.stats.stats.max
    if stat > TRACER_INIT_SLA:
        pytest.fail(f"High level imports should be below {TRACER_INIT_SLA}s: {stat}")


@pytest.mark.perf
@pytest.mark.benchmark(group="core", disable_gc=True, warmup=False)
def test_metrics_init(benchmark):
    # GIVEN Metrics is initialized
    # WHEN default options are used
    # THEN initialization perf should be below 5ms
    benchmark.pedantic(import_init_metrics)
    stat = benchmark.stats.stats.max
    if stat > METRICS_INIT_SLA:
        pytest.fail(f"High level imports should be below ${METRICS_INIT_SLA}s: {stat}")


@pytest.mark.perf
@pytest.mark.benchmark(group="core", disable_gc=True, warmup=False)
def test_logger_init(benchmark):
    # GIVEN Logger is initialized
    # WHEN default options are used
    # THEN initialization perf should be below 5ms
    benchmark.pedantic(import_init_logger)
    stat = benchmark.stats.stats.max
    if stat > LOGGER_INIT_SLA:
        pytest.fail(f"High level imports should be below ${LOGGER_INIT_SLA}s: {stat}")
