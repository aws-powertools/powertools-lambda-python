from aws_lambda_powertools.metrics.provider.cloudwatch_emf.exceptions import MetricResolutionError, MetricUnitError


class SchemaValidationError(Exception):
    """When serialization fail schema validation"""

    pass


class MetricValueError(Exception):
    """When metric value isn't a valid number"""

    pass


__all__ = ["MetricUnitError", "MetricResolutionError", "SchemaValidationError", "MetricValueError"]
