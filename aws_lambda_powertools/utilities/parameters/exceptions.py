"""
Parameter retrieval exceptions
"""


class GetParameterError(Exception):
    """When a provider raises an exception on parameter retrieval"""


class TransformParameterError(Exception):
    """When a provider fails to transform a parameter value"""
