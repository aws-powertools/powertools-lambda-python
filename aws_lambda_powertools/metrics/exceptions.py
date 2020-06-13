class MetricUnitError(Exception):
    """When metric unit is not supported by CloudWatch"""

    pass


class SchemaValidationError(Exception):
    """When serialization fail schema validation"""

    pass


class MetricValueError(Exception):
    """When metric value isn't a valid number"""

    pass
