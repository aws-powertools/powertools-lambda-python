from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from aws_lambda_powertools.utilities.parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.parser.models import KinesisFirehoseModel

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser.types import Model

logger = logging.getLogger(__name__)


class KinesisFirehoseEnvelope(BaseEnvelope):
    """Kinesis Firehose Envelope to extract array of Records

    The record's data parameter is a base64 encoded string which is parsed into a bytes array,
    though it can also be a JSON encoded string.
    Regardless of its type it'll be parsed into a BaseModel object.

    Note: Records will be parsed the same way so if model is str,
    all items in the list will be parsed as str and not as JSON (and vice versa)

    https://docs.aws.amazon.com/lambda/latest/dg/services-kinesisfirehose.html
    """

    def parse(self, data: dict[str, Any] | Any | None, model: type[Model]) -> list[Model | None]:
        """Parses records found with model provided

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
        logger.debug(f"Parsing incoming data with Kinesis Firehose model {KinesisFirehoseModel}")
        parsed_envelope: KinesisFirehoseModel = KinesisFirehoseModel.model_validate(data)
        logger.debug(f"Parsing Kinesis Firehose records in `body` with {model}")
        models = []
        for record in parsed_envelope.records:
            # We allow either AWS expected contract (bytes) or a custom Model, see #943
            data = cast(bytes, record.data)
            models.append(self._parse(data=data.decode("utf-8"), model=model))
        return models
