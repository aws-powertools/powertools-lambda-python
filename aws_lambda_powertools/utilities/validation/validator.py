import json
import logging
from typing import Any, Callable, Dict, Union

from ...middleware_factory import lambda_handler_decorator
from .base import unwrap_event_from_envelope, validate_data_against_schema

logger = logging.getLogger(__name__)


@lambda_handler_decorator
def validator(
    handler: Callable,
    event: Union[Dict, str],
    context: Any,
    inbound_schema: Dict = None,
    outbound_schema: Dict = None,
    envelope: str = None,
    jmespath_options: Dict = None,
):
    if isinstance(event, str):
        event = json.loads(event)

    if envelope:
        event = unwrap_event_from_envelope(data=event, envelope=envelope, jmespath_options=jmespath_options)

    if inbound_schema:
        logger.debug("Validating inbound event")
        validate_data_against_schema(data=event, schema=inbound_schema)

    response = handler(event, context)

    if outbound_schema:
        logger.debug("Validating outbound event")
        validate_data_against_schema(data=event, schema=outbound_schema)

    return response


def validate(event: Dict, schema: Dict = None, envelope: str = None, jmespath_options: Dict = None):
    if envelope:
        event = unwrap_event_from_envelope(data=event, envelope=envelope, jmespath_options=jmespath_options)

    if isinstance(event, str):
        event = json.loads(event)

    validate_data_against_schema(data=event, schema=schema)
