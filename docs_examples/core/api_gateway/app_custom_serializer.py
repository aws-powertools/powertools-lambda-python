import json
from enum import Enum
from json import JSONEncoder
from typing import Dict

from aws_lambda_powertools.event_handler import APIGatewayRestResolver


class CustomEncoder(JSONEncoder):
    """Your customer json encoder"""

    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        try:
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return sorted(iterable)
        return JSONEncoder.default(self, obj)


def custom_serializer(obj) -> str:
    """Your custom serializer function APIGatewayRestResolver will use"""
    return json.dumps(obj, cls=CustomEncoder)


# Assigning your custom serializer
app = APIGatewayRestResolver(serializer=custom_serializer)


class Color(Enum):
    RED = 1
    BLUE = 2


@app.get("/colors")
def get_color() -> Dict:
    return {
        # Color.RED will be serialized to 1 as expected now
        "color": Color.RED,
        "variations": {"light", "dark"},
    }
