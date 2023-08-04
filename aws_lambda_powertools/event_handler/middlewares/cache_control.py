from typing import Callable, Optional

from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, Response
from aws_lambda_powertools.event_handler.middlewares.base import BaseMiddlewareHandler


class CacheControlMiddleware(BaseMiddlewareHandler):
    """
    CacheControlMiddleware adds Cache-Control header to responses with status code 200.
    """

    def __init__(self, cache_control: Optional[str] = None):
        self.cache_control = cache_control

    def __call__(self, app: ApiGatewayResolver, get_response: Callable, **kwargs) -> Response:
        # Modify request details here before calling handler

        # Call Handler and get response
        result: Response = get_response(app, **kwargs)

        # Modify Response from Handler here before returning
        cache_control = self.cache_control if result.status_code == 200 else "no-cache"
        result.headers["Cache-Control"] = cache_control or ""

        return result
