from typing import Any, Callable

from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler.api_gateway import BaseRouter


def middleware_func(app: BaseRouter, get_response: Callable[..., Any], **context_args) -> Response:
    # Do Before processing here

    # Get Next response
    result = get_response(app, **context_args)

    # Do After processing here

    # return the response
    return result
