import logging
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.advanced_parser.envelopes import Envelope, parse_envelope

logger = logging.getLogger(__name__)


@lambda_handler_decorator
def parser(
    handler: Callable[[Dict, Any], Any],
    event: Dict[str, Any],
    context: Dict[str, Any],
    schema: BaseModel,
    envelope: Optional[Envelope] = None,
) -> Any:
    """Decorator to conduct advanced parsing & validation for lambda handlers events

        As Lambda follows (event, context) signature we can remove some of the boilerplate
        and also capture any exception any Lambda function throws as metadata.
        Event will be the parsed & validated BaseModel pydantic object of the input type "schema"

        Example
        -------
        **Lambda function using validation decorator**

            @parser(schema=MyBusiness, envelope=envelopes.EVENTBRIDGE)
            def handler(event: inbound_schema_model , context: LambdaContext):
                ...

        Parameters
        ----------
        todo add

        Raises
        ------
        err
            TypeError or pydantic.ValidationError or any exception raised by the lambda handler itself
    """
    lambda_handler_name = handler.__name__
    parsed_event = None
    if envelope is None:
        try:
            logger.debug("Parsing and validating event schema, no envelope is used")
            parsed_event = schema(**event)
        except (ValidationError, TypeError):
            logger.exception("Validation exception received from input event")
            raise
    else:
        parsed_event = parse_envelope(event, envelope, schema)

    logger.debug(f"Calling handler {lambda_handler_name}")
    handler(parsed_event, context)
