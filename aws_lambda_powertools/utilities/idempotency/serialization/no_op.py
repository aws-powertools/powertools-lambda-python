from typing import Dict

from aws_lambda_powertools.utilities.idempotency.serialization.base import BaseIdempotencySerializer


class NoOpSerializer(BaseIdempotencySerializer):
    def __init__(self):
        """
        Parameters
        ----------
        Default serializer, does not transform data
        """

    def to_dict(self, data: Dict) -> Dict:
        return data

    def from_dict(self, data: Dict) -> Dict:
        return data
