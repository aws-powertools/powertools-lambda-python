import logging
from typing import Callable

logger = logging.getLogger(__name__)


# Note: Type hinting not available due to cyclic dependency between api_gateway.py and this module
def registered_api_middleware(app, get_response: Callable, **kwargs):
    """
    Call the registered API using the **kwargs provided.

    :param app: The API Gateway resolver
    :param get_response: The function to handle the API
    :param kwargs: The arguments to pass to the API
    :return: The API Response Object

    This middleware enables backward compatibility for the existing API routes model in Powertools
    and it MUST be the final middleware in the middleware stack.
    """
    return app._to_response(get_response(**kwargs))
