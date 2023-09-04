import logging
from typing import Dict, Optional

from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, NextMiddlewareCallback, Response
from aws_lambda_powertools.event_handler.exceptions import BadRequestError, InternalServerError
from aws_lambda_powertools.event_handler.middlewares import BaseMiddlewareHandler
from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.validation.exceptions import InvalidSchemaFormatError, SchemaValidationError

logger = logging.getLogger(__name__)


class SchemaValidationMiddleware(BaseMiddlewareHandler):
    """
    Validates the API request body against the provided schema.

    """

    def __init__(
        self,
        inbound_schema: Dict,
        inbound_formats: Optional[Dict] = None,
        outbound_schema: Optional[Dict] = None,
        outbound_formats: Optional[Dict] = None,
    ):
        super().__init__()
        self.inbound_schema = inbound_schema
        self.inbound_formats = inbound_formats
        self.outbound_schema = outbound_schema
        self.outbound_formats = outbound_formats

    def bad_response(self, error: SchemaValidationError) -> Response:
        message: str = f"Bad Response: {error.message}"
        logger.debug(message)
        raise BadRequestError(message)

    def bad_request(self, error: SchemaValidationError) -> Response:
        message: str = f"Bad Request: {error.message}"
        logger.debug(message)
        raise BadRequestError(message)

    def bad_config(self, error: InvalidSchemaFormatError) -> Response:
        logger.debug(f"Invalid Schema Format: {error}")
        raise InternalServerError("Internal Server Error")

    def handler(self, app: ApiGatewayResolver, next_middleware: NextMiddlewareCallback) -> Response:
        """
        Validate using Powertools validate() utility.

        Return HTTP 400 Response if validation fails.
        Return HTTP 500 Response if validation fails due to invalid schema format.

        Return the next middleware response if validation passes.

        :param app: The ApiGatewayResolver instance
        :param next_middleware: The original response
        :return: The original response or HTTP 400 Response or HTTP 500 Response.

        """
        try:
            validate(event=app.current_event.json_body, schema=self.inbound_schema, formats=self.inbound_formats)
        except SchemaValidationError as error:
            return self.bad_request(error)
        except InvalidSchemaFormatError as error:
            return self.bad_config(error)

        # return next middleware response if validation passes.
        result: Response = next_middleware(app)

        if self.outbound_formats is not None:
            try:
                validate(event=result.body, schema=self.inbound_schema, formats=self.inbound_formats)
            except SchemaValidationError as error:
                return self.bad_response(error)
            except InvalidSchemaFormatError as error:
                return self.bad_config(error)

        return result
