import decimal
import json
import math


class Encoder(json.JSONEncoder):
    """Custom JSON encoder to allow for serialization of Decimals, Pydantic and Dataclasses.

    It's similar to the serializer used by Lambda internally.
    """

    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            if obj.is_nan():
                return math.nan
            return str(obj)

        # Pydantic model (v1/v2)
        if hasattr(obj, "json"):
            from aws_lambda_powertools.event_handler.openapi.compat import _model_dump

            return _model_dump(obj)

        # Standard dataclass
        if hasattr(obj, "__dataclass_fields__"):
            import dataclasses

            return dataclasses.asdict(obj)

        return super().default(obj)
