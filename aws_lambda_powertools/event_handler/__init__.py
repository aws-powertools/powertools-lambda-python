"""
Event handler decorators for common Lambda events
"""

from .api_gateway import ApiGatewayResolver
from .appsync import AppSyncResolver

__all__ = ["AppSyncResolver", "ApiGatewayResolver"]
