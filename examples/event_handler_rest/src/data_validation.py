from typing import Optional

import requests
from pydantic import BaseModel, Field

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayHttpResolver(enable_validation=True)  # (1)!


class Todo(BaseModel):  # (2)!
    userId: int
    id_: Optional[int] = Field(alias="id", default=None)
    title: str
    completed: bool


@app.get("/todos/<todo_id>")  # (3)!
@tracer.capture_method
def get_todo_by_id(todo_id: int) -> Todo:  # (4)!
    todo = requests.get(f"https://jsonplaceholder.typicode.com/todos/{todo_id}")
    todo.raise_for_status()

    return Todo(**todo.json())  # (5)!


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
