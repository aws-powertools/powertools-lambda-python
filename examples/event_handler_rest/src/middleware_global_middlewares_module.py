from typing import Callable

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response

logger = Logger()


def log_request_response(app: APIGatewayRestResolver, get_response: Callable[..., Response], **context) -> Response:
    logger.info("Incoming request", path=app.current_event.path, request=app.current_event.raw_event)

    result = get_response(app, **context)
    logger.info("Response received", response=result.__dict__)

    return result


def inject_correlation_id(app: APIGatewayRestResolver, get_response: Callable[..., Response], **context) -> Response:
    request_id = app.current_event.request_context.request_id

    # Use API Gateway REST API request ID if caller didn't include a correlation ID
    correlation_id = app.current_event.headers.get("x-correlation-id", request_id)

    # Inject correlation ID in shared context and Logger
    app.append_context(correlation_id=correlation_id)
    logger.set_correlation_id(request_id)

    # Get response from next middleware OR /todos route
    result = get_response(app, **context)

    # Include Correlation ID in the response back to caller
    result.headers["x-correlation-id"] = correlation_id
    return result
