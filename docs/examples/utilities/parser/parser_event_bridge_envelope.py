from typing import Any, Dict, Optional, TypeVar, Union

from aws_lambda_powertools.utilities.parser import BaseEnvelope, BaseModel
from aws_lambda_powertools.utilities.parser.models import EventBridgeModel

Model = TypeVar("Model", bound=BaseModel)


class EventBridgeEnvelope(BaseEnvelope):
    def parse(self, data: Optional[Union[Dict[str, Any], Any]], model: Model) -> Optional[Model]:
        """Parses data found with model provided

        Parameters
        ----------
        data : Dict
            Lambda event to be parsed
        model : Model
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        Any
            Parsed detail payload with model provided
        """
        parsed_envelope = EventBridgeModel.parse_obj(data)
        return self._parse(data=parsed_envelope.detail, model=model)
