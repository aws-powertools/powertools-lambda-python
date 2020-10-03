import logging
from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel

from aws_lambda_powertools.utilities.advanced_parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.advanced_parser.envelopes.dynamodb import DynamoDBEnvelope
from aws_lambda_powertools.utilities.advanced_parser.envelopes.event_bridge import EventBridgeEnvelope
from aws_lambda_powertools.utilities.advanced_parser.envelopes.sqs import SqsEnvelope

logger = logging.getLogger(__name__)


"""Built-in envelopes"""


class Envelope(str, Enum):
    SQS = "sqs"
    EVENTBRIDGE = "eventbridge"
    DYNAMODB_STREAM = "dynamodb_stream"


class InvalidEnvelopeError(Exception):
    """Input envelope is not one of the Envelope enum values"""


# enum to BaseEnvelope handler class
__ENVELOPE_MAPPING = {
    Envelope.SQS: SqsEnvelope,
    Envelope.DYNAMODB_STREAM: DynamoDBEnvelope,
    Envelope.EVENTBRIDGE: EventBridgeEnvelope,
}


def parse_envelope(event: Dict[str, Any], envelope: Envelope, schema: BaseModel):
    envelope_handler: BaseEnvelope = __ENVELOPE_MAPPING.get(envelope)
    if envelope_handler is None:
        logger.exception("envelope must be an instance of Envelope enum")
        raise InvalidEnvelopeError("envelope must be an instance of Envelope enum")
    logger.debug(f"Parsing and validating event schema, envelope={str(envelope.value)}")
    return envelope_handler().parse(event=event, schema=schema)
