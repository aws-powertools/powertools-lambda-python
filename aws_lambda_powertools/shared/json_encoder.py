import decimal
import json
import math


class Encoder(json.JSONEncoder):
    """
    Custom JSON encoder to allow for serialization of Decimals, similar to the serializer used by Lambda internally.
    """

    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            if obj.is_nan():
                return math.nan
            return str(obj)
        return super().default(obj)
