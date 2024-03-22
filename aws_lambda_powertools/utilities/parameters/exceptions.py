"""
Parameter retrieval exceptions
"""


class GetParameterError(Exception):
    """When a provider raises an exception on parameter retrieval"""


class TransformParameterError(Exception):
    """When a provider fails to transform a parameter value"""


class SetParameterError(Exception):
    """When a provider raises an exception on writing a SSM parameter"""


class SetSecretError(Exception):
    """When a provider raises an exception on writing a secret"""
