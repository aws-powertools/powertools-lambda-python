class InvalidTracerProviderError(Exception):
    """When given provider doesn't implement `aws_lambda_powertools.tracing.base.TracerProvider`"""

    pass


class TracerProviderNotInitializedError(Exception):
    """When given provider isn't initialized/bound"""

    pass
