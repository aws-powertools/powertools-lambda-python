"""Utilities to enhance middlewares
!!! abstract "Usage Documentation"
    [`Middleware Factory`](../utilities/middleware_factory.md)
"""

from .factory import lambda_handler_decorator

__all__ = ["lambda_handler_decorator"]
