import json
from typing import Any, Callable, Dict, Optional

from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, Response
from aws_lambda_powertools.event_handler.middlewares import BaseMiddlewareHandler
from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.validation.exceptions import InvalidSchemaFormatError, SchemaValidationError


class SchemaValidationMiddleware(BaseMiddlewareHandler):
    """
    Validates the API request body against the provided schema.

    """

    def __init__(self, schema: Dict, formats: Optional[Dict] = None):
        super().__init__()
        self.schema = schema
        self.formats = formats

    def bad_request(self, error: SchemaValidationError) -> Response:
        return Response(
            status_code=400,
            content_type=content_types.APPLICATION_JSON,
            body=json.dumps({"message": error.message}),
        )

    def bad_config(self, error: InvalidSchemaFormatError) -> Response:
        return Response(
            status_code=500,
            content_type=content_types.APPLICATION_JSON,
            body=json.dumps({"message": str(error)}),
        )

    def handler(self, app: ApiGatewayResolver, get_response: Callable[..., Any], **kwargs) -> Response:
        """
        Validate using Powertools validate() utility.

        Return HTTP 400 Response if validation fails.
        Return HTTP 500 Response if validation fails due to invalid schema format.

        Return the next middleware response if validation passes.

        :param app: The ApiGatewayResolver instance
        :param get_response: The original response
        :param kwargs: Additional arguments
        :return: The original response or HTTP 400 Response or HTTP 500 Response.

        """
        try:
            validate(event=app.current_event.json_body, schema=self.schema, formats=self.formats)
        except SchemaValidationError as error:
            return self.bad_request(error)
        except InvalidSchemaFormatError as error:
            return self.bad_config(error)

        # return next middleware response if validation passes.
        return get_response(app, **kwargs)
