class MetricUnitError(Exception):
    """When metric unit is not supported by CloudWatch"""

    pass


class MetricResolutionError(Exception):
    """When metric resolution is not supported by CloudWatch"""

    pass
