from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.types import NextMiddlewareCallback

logger = Logger()


def log_request_response(app: APIGatewayRestResolver, next_middleware: NextMiddlewareCallback) -> Response:
    logger.info("Incoming request", path=app.current_event.path, request=app.current_event.raw_event)

    result = next_middleware(app)
    logger.info("Response received", response=result.__dict__)

    return result


def inject_correlation_id(app: APIGatewayRestResolver, next_middleware: NextMiddlewareCallback) -> Response:
    request_id = app.current_event.request_context.request_id

    # Use API Gateway REST API request ID if caller didn't include a correlation ID
    correlation_id = app.current_event.headers.get("x-correlation-id", request_id)

    # Inject correlation ID in shared context and Logger
    app.append_context(correlation_id=correlation_id)
    logger.set_correlation_id(request_id)

    # Get response from next middleware OR /todos route
    result = next_middleware(app)

    # Include Correlation ID in the response back to caller
    result.headers["x-correlation-id"] = correlation_id
    return result


def enforce_correlation_id(app: APIGatewayRestResolver, next_middleware: NextMiddlewareCallback) -> Response:
    # If missing mandatory header raise an error
    if not app.current_event.get_header_value("x-correlation-id", case_sensitive=False):
        return Response(status_code=400, body="Correlation ID header is now mandatory.")  # (1)!

    # Get the response from the next middleware and return it
    return next_middleware(app)
