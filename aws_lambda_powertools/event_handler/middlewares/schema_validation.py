import logging
from typing import Dict, Optional

from aws_lambda_powertools.event_handler.api_gateway import Response
from aws_lambda_powertools.event_handler.exceptions import BadRequestError, InternalServerError
from aws_lambda_powertools.event_handler.middlewares import BaseMiddlewareHandler, NextMiddleware
from aws_lambda_powertools.event_handler.types import EventHandlerInstance
from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.validation.exceptions import InvalidSchemaFormatError, SchemaValidationError

logger = logging.getLogger(__name__)


class SchemaValidationMiddleware(BaseMiddlewareHandler):
    """Middleware to validate API request and response against JSON Schema using the [Validation utility](https://docs.powertools.aws.dev/lambda/python/latest/utilities/validation/).

    Examples
    --------
    **Validating incoming event**

    ```python
    import requests

    from aws_lambda_powertools import Logger
    from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
    from aws_lambda_powertools.event_handler.middlewares import BaseMiddlewareHandler, NextMiddleware
    from aws_lambda_powertools.event_handler.middlewares.schema_validation import SchemaValidationMiddleware

    app = APIGatewayRestResolver()
    logger = Logger()
    json_schema_validation = SchemaValidationMiddleware(inbound_schema=INCOMING_JSON_SCHEMA)


    @app.get("/todos", middlewares=[json_schema_validation])
    def get_todos():
        todos: requests.Response = requests.get("https://jsonplaceholder.typicode.com/todos")
        todos.raise_for_status()

        # for brevity, we'll limit to the first 10 only
        return {"todos": todos.json()[:10]}


    @logger.inject_lambda_context
    def lambda_handler(event, context):
        return app.resolve(event, context)
    ```
    """

    def __init__(
        self,
        inbound_schema: Dict,
        inbound_formats: Optional[Dict] = None,
        outbound_schema: Optional[Dict] = None,
        outbound_formats: Optional[Dict] = None,
    ):
        """See [Validation utility](https://docs.powertools.aws.dev/lambda/python/latest/utilities/validation/) docs for examples on all parameters.

        Parameters
        ----------
        inbound_schema : Dict
            JSON Schema to validate incoming event
        inbound_formats : Optional[Dict], optional
            Custom formats containing a key (e.g. int64) and a value expressed as regex or callback returning bool, by default None
            JSON Schema to validate outbound event, by default None
        outbound_formats : Optional[Dict], optional
            Custom formats containing a key (e.g. int64) and a value expressed as regex or callback returning bool, by default None
        """  # noqa: E501
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

    def handler(self, app: EventHandlerInstance, next_middleware: NextMiddleware) -> Response:
        """Validates incoming JSON payload (body) against JSON Schema provided.

        Parameters
        ----------
        app : EventHandlerInstance
            An instance of an Event Handler
        next_middleware : NextMiddleware
            Callable to get response from the next middleware or route handler in the chain

        Returns
        -------
        Response
            It can return three types of response objects

            - Original response: Propagates HTTP response returned from the next middleware if validation succeeds
            - HTTP 400: Payload or response failed JSON Schema validation
            - HTTP 500: JSON Schema provided has incorrect format
        """
        try:
            validate(event=app.current_event.json_body, schema=self.inbound_schema, formats=self.inbound_formats)
        except SchemaValidationError as error:
            return self.bad_request(error)
        except InvalidSchemaFormatError as error:
            return self.bad_config(error)

        result = next_middleware(app)

        if self.outbound_formats is not None:
            try:
                validate(event=result.body, schema=self.inbound_schema, formats=self.inbound_formats)
            except SchemaValidationError as error:
                return self.bad_response(error)
            except InvalidSchemaFormatError as error:
                return self.bad_config(error)

        return result
