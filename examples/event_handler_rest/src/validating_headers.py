from typing import List, Optional

import requests
from pydantic import BaseModel, Field

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import Header  # (2)!
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.shared.types import Annotated  # (1)!
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver(enable_validation=True)


class Todo(BaseModel):
    userId: int
    id_: Optional[int] = Field(alias="id", default=None)
    title: str
    completed: bool


@app.get("/todos")
@tracer.capture_method
def get_todos(correlation_id: Annotated[str, Header(min_length=16, max_length=16)]) -> List[Todo]:  # (3)!
    url = "https://jsonplaceholder.typicode.com/todos"

    todo = requests.get(url, headers={"correlation_id": correlation_id})
    todo.raise_for_status()

    return todo.json()


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
