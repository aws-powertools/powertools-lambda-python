import decimal
import json
import math

from aws_lambda_powertools.shared.functions import dataclass_to_dict, is_dataclass, is_pydantic, pydantic_to_dict


class Encoder(json.JSONEncoder):
    """Custom JSON encoder to allow for serialization of Decimals, Pydantic and Dataclasses.

    It's similar to the serializer used by Lambda internally.
    """

    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            if obj.is_nan():
                return math.nan
            return str(obj)

        if is_pydantic(obj):
            return pydantic_to_dict(obj)

        if is_dataclass(obj):
            return dataclass_to_dict(obj)

        return super().default(obj)
