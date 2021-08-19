"""Shared exceptions that don't belong to a single utility"""


class InvalidEnvelopeExpressionError(Exception):
    """When JMESPath fails to parse expression"""
