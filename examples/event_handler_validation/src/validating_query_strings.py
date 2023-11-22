from typing import Annotated, Optional

import requests
from pydantic import BaseModel, Field

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.openapi.params import Query
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayHttpResolver(enable_validation=True)


class Todo(BaseModel):
    userId: int
    id_: Optional[int] = Field(alias="id", default=None)
    title: str
    completed: bool


@app.get("/todos")
@tracer.capture_method
def get_todos(completed: Annotated[Optional[str], Query(min_length=4)] = None) -> Todo:
    url = "https://jsonplaceholder.typicode.com/todos"

    if completed is not None:
        url = f"{url}/?completed={completed}"

    todo = requests.get(url)
    todo.raise_for_status()

    return Todo(**todo.json()[0])


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
