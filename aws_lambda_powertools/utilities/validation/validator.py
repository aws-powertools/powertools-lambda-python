import logging
from typing import Any, Callable, Dict

from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.validation.envelopes.base import BaseEnvelope

logger = logging.getLogger(__name__)


@lambda_handler_decorator
def validator(
    handler: Callable[[Dict, Any], Any],
    event: Dict[str, Any],
    context: Dict[str, Any],
    inbound_schema_model: BaseModel,
    outbound_schema_model: BaseModel,
    envelope: BaseEnvelope,
) -> Any:
    """Decorator to create validation for lambda handlers events - both inbound and outbound

        As Lambda follows (event, context) signature we can remove some of the boilerplate
        and also capture any exception any Lambda function throws or its response as metadata

        Example
        -------
        **Lambda function using validation decorator**

            @validator(inbound=inbound_schema_model, outbound=outbound_schema_model)
            def handler(parsed_event_model, context):
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
    logger.debug("Validating inbound schema")
    parsed_event_model = envelope.parse(event, inbound_schema_model)
    try:
        logger.debug(f"Calling handler {lambda_handler_name}")
        response = handler({"orig": event, "custom": parsed_event_model}, context)
        logger.debug("Received lambda handler response successfully")
        logger.debug(response)
    except Exception:
        logger.exception(f"Exception received from {lambda_handler_name}")
        raise

    try:
        logger.debug("Validating outbound response schema")
        outbound_schema_model(**response)
    except (ValidationError, TypeError):
        logger.exception(f"Validation exception received from {lambda_handler_name} response event")
        raise
    return response
