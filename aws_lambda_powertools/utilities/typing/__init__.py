# -*- coding: utf-8 -*-

"""
Typing for developer ease in the IDE

> This is copied from: https://gist.github.com/alexcasalboni/a545b68ee164b165a74a20a5fee9d133
"""

from .lambda_client_context import LambdaClientContext
from .lambda_client_context_mobile_client import LambdaClientContextMobileClient
from .lambda_cognito_identity import LambdaCognitoIdentity
from .lambda_context import LambdaContext
from .lambda_dict import LambdaDict

__all__ = [
    "LambdaDict",
    "LambdaClientContext",
    "LambdaClientContextMobileClient",
    "LambdaCognitoIdentity",
    "LambdaContext",
]
