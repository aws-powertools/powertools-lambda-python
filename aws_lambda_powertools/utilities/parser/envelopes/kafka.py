from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from aws_lambda_powertools.utilities.parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.parser.models import KafkaMskEventModel, KafkaSelfManagedEventModel

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser.types import Model

logger = logging.getLogger(__name__)


class KafkaEnvelope(BaseEnvelope):
    """Kafka event envelope to extract data within body key
    The record's body parameter is a string, though it can also be a JSON encoded string.
    Regardless of its type it'll be parsed into a BaseModel object.

    Note: Records will be parsed the same way so if model is str,
    all items in the list will be parsed as str and npt as JSON (and vice versa)
    """

    def parse(self, data: dict[str, Any] | Any | None, model: type[Model]) -> list[Model | None]:
        """Parses data found with model provided

        Parameters
        ----------
        data : dict
            Lambda event to be parsed
        model : type[Model]
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        list
            List of records parsed with model provided
        """
        event_source = cast(dict, data).get("eventSource")
        model_parse_event: type[KafkaMskEventModel | KafkaSelfManagedEventModel] = (
            KafkaMskEventModel if event_source == "aws:kafka" else KafkaSelfManagedEventModel
        )

        logger.debug(f"Parsing incoming data with Kafka event model {model_parse_event}")
        parsed_envelope = model_parse_event.model_validate(data)
        logger.debug(f"Parsing Kafka event records in `value` with {model}")
        ret_list = []
        for records in parsed_envelope.records.values():
            ret_list += [self._parse(data=record.value, model=model) for record in records]
        return ret_list
