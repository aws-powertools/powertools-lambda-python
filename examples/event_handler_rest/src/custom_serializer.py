import json
from dataclasses import asdict, dataclass, is_dataclass
from json import JSONEncoder

import requests
from requests import Response

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()


@dataclass
class Todo:
    userId: str
    id: str  # noqa: A003 VNE003 "id" field is reserved
    title: str
    completed: bool


class DataclassCustomEncoder(JSONEncoder):
    """A custom JSON encoder to serialize dataclass obj"""

    def default(self, obj):
        # Only called for values that aren't JSON serializable
        # where `obj` will be an instance of Todo in this example
        return asdict(obj) if is_dataclass(obj) else super().default(obj)


def custom_serializer(obj) -> str:
    """Your custom serializer function APIGatewayRestResolver will use"""
    return json.dumps(obj, separators=(",", ":"), cls=DataclassCustomEncoder)


app = APIGatewayRestResolver(serializer=custom_serializer)


@app.get("/todos")
@tracer.capture_method
def get_todos():
    ret: Response = requests.get("https://jsonplaceholder.typicode.com/todos")
    ret.raise_for_status()
    todos = [Todo(**todo) for todo in ret.json()]

    # for brevity, we'll limit to the first 10 only
    return {"todos": todos[:10]}


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
