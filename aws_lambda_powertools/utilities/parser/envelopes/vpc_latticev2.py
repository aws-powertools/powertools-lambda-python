import logging
from typing import Any, Dict, Optional, Type, Union

from ..models import VpcLatticeV2Model
from ..types import Model
from .base import BaseEnvelope

logger = logging.getLogger(__name__)


class VpcLatticeV2Envelope(BaseEnvelope):
    """Amazon VPC Lattice envelope to extract data within body key"""

    def parse(self, data: Optional[Union[Dict[str, Any], Any]], model: Type[Model]) -> Optional[Model]:
        """Parses data found with model provided

        Parameters
        ----------
        data : Dict
            Lambda event to be parsed
        model : Type[Model]
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        Optional[Model]
            Parsed detail payload with model provided
        """
        logger.debug(f"Parsing incoming data with VPC Lattice V2 model {VpcLatticeV2Model}")
        parsed_envelope: VpcLatticeV2Model = VpcLatticeV2Model.parse_obj(data)
        logger.debug(f"Parsing event payload in `detail` with {model}")
        return self._parse(data=parsed_envelope.body, model=model)
