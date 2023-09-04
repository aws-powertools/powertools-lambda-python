from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import ApiGatewayResolver, Response
from aws_lambda_powertools.event_handler.api_gateway import NextMiddlewareCallback
from aws_lambda_powertools.event_handler.exceptions import BadRequestError, InternalServerError, ServiceError

logger = Logger()


def validate_correlation_id(app: ApiGatewayResolver, next_middleware: NextMiddlewareCallback) -> Response:
    # If missing mandatory header raise an error
    if not app.current_event.headers.get("x-correlation-id", None):
        raise BadRequestError("No [x-correlation-id] header provided.  All requests must include this header.")

    # Get the response from the next middleware and return it
    return next_middleware(app)


def sanitise_exceptions(app: ApiGatewayResolver, next_middleware: NextMiddlewareCallback) -> Response:
    try:
        # Get the Result from the next middleware
        result = next_middleware(app)
    except Exception as err:
        logger.exception(err)
        # Raise a clean error for ALL unexpected exceptions (ServiceError based Exceptions are okay)
        if not isinstance(err, ServiceError):
            raise InternalServerError("An error occurred during processing, please contact your administrator") from err

        raise err

    # return the result when there are no exceptions
    return result
