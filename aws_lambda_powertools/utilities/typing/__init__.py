# -*- coding: utf-8 -*-

"""
Typing for developer ease in the IDE

> This is copied from: https://gist.github.com/alexcasalboni/a545b68ee164b165a74a20a5fee9d133
"""

from .event import LambdaEvent
from .lambda_context import LambdaContext

__all__ = [
    "LambdaEvent",
    "LambdaContext",
]
