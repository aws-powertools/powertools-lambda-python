from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser.types import Model

logger = logging.getLogger(__name__)


class ApiGatewayEnvelope(BaseEnvelope):
    """API Gateway envelope to extract data within body key"""

    def parse(self, data: dict[str, Any] | Any | None, model: type[Model]) -> Model | None:
        """Parses data found with model provided

        Parameters
        ----------
        data : dict
            Lambda event to be parsed
        model : type[Model]
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        Any
            Parsed detail payload with model provided
        """
        logger.debug(f"Parsing incoming data with Api Gateway model {APIGatewayProxyEventModel}")
        parsed_envelope: APIGatewayProxyEventModel = APIGatewayProxyEventModel.model_validate(data)
        logger.debug(f"Parsing event payload in `detail` with {model}")
        return self._parse(data=parsed_envelope.body, model=model)
